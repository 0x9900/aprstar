#!/usr/bin/python3
# pylint: disable=missing-docstring

import json
import logging
import os
import platform
import sys
import time

from configparser import ConfigParser
from io import StringIO

import aprslib

try:                            # Python 3
  from urllib.request import urlopen
except ImportError:             # Python 2
  from urllib import urlopen

from aprslib.exceptions import ConnectionError

CONFIG_FILE = "/etc/aprstar.conf"
CONFIG_DEFAULT = u"""
[APRS]
call: N0CALL-1
latitude: 0
longitude: 0
sleep: 600
symbol: n
symbol_table: /
"""

THERMAL_FILE = "/sys/class/thermal/thermal_zone0/temp"
LOADAVG_FILE = "/proc/loadavg"
DEFAULT_PORT = 14580

logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)


class Config(object):

  def __init__(self):
    parser = ConfigParser()
    parser.read_file(StringIO(CONFIG_DEFAULT))

    self._passcode = ""
    self._call = "NOCALL-1"
    self._longitude = 0.0
    self._latitude = 0.0
    self._sleep = 900
    self._symbol = "n"
    self._symbol_table = "/"

    if not os.path.exists(CONFIG_FILE):
      logging.info('Using default config')
    else:
      try:
        logging.info('Reading config file')
        with open(CONFIG_FILE, 'r') as fdc:
          parser.readfp(fdc)
        logging.info('Config file %s read', CONFIG_FILE)
      except (IOError, SystemError):
        raise SystemError('No [APRS] section configured')

    self.call = parser.get('APRS', 'call')
    self.sleep = parser.get('APRS', 'sleep')
    self.symbol_table = parser.get('APRS', 'symbol_table')
    self.symbol = parser.get('APRS', 'symbol')

    lat, lon = [float(parser.get('APRS', c)) for c in ('latitude', 'longitude')]
    if not lat or not lon:
      self.latitude, self.longitude = get_coordinates()
    else:
      self.latitude, self.longitude = lat, lon

    if parser.has_option('APRS', 'passcode'):
      self.passcode = parser.get('APRS', 'passcode')
    else:
      logging.warning('Generating passcode')
      self.passcode = aprslib.passcode(self.call)

  def __repr__(self):
    return ("<Config> call: {0.call}, passcode: {0.passcode} - "
            "{0.latitude}/{0.longitude}").format(self)

  @property
  def call(self):
    return self._call

  @call.setter
  def call(self, val):
    self._call = str(val)

  @property
  def sleep(self):
    return self._sleep

  @sleep.setter
  def sleep(self, val):
    try:
      self._sleep = int(val)
    except ValueError:
      logging.warning('Sleep value error using 600')
      self._sleep = 600

  @property
  def latitude(self):
    return self._latitude

  @latitude.setter
  def latitude(self, val):
    self._latitude = val

  @property
  def longitude(self):
    return self._longitude

  @longitude.setter
  def longitude(self, val):
    self._longitude = val

  @property
  def passcode(self):
    return self._passcode

  @passcode.setter
  def passcode(self, val):
    self._passcode = str(val)

  @property
  def symbol(self):
    return self._symbol

  @symbol.setter
  def symbol(self, val):
    self._symbol = str(val)

  @property
  def symbol_table(self):
    return self._symbol_table

  @symbol_table.setter
  def symbol_table(self, val):
    self._symbol_table = str(val)


class Sequence(object):
  """Generate an APRS sequence number."""
  def __init__(self):
    self.sequence_file = '/tmp/aprstar.sequence'
    try:
      with open(self.sequence_file) as fds:
        self._count = int(fds.readline())
    except (IOError, ValueError):
      self._count = 0

  def flush(self):
    try:
      with open(self.sequence_file, 'w') as fds:
        fds.write("{0:d}".format(self._count))
    except IOError:
      pass

  def __iter__(self):
    return self

  def next(self):
    return self.__next__()

  def __next__(self):
    self._count = (1 + self._count) % 999
    self.flush()
    return self._count


def get_coordinates():
  logging.warning('Trying to figure out the coordinate using your IP address')
  url = "http://ip-api.com/json/"
  try:
    response = urlopen(url)
    _data = response.read()
    data = json.loads(_data.decode())
  except IOError as err:
    logging.error(err)
    return (0, 0)
  else:
    logging.warning('Position: %f, %f', data['lat'], data['lon'])
    return data['lat'], data['lon']


def get_load():
  try:
    with open(LOADAVG_FILE) as lfd:
      loadstr = lfd.readline()
  except IOError:
    return 0

  try:
    load15 = float(loadstr.split()[1])
  except ValueError:
    return 0

  return int(load15 * 1000)


def get_freemem():
  proc_file = '/proc/meminfo'
  try:
    with open(proc_file) as pfd:
      for line in pfd:
        if 'MemFree' in line:
          freemem = int(line.split()[1])
  except (IOError, ValueError):
    return 0

  return int(freemem / 1024)


def get_temp():
  try:
    with open(THERMAL_FILE) as tfd:
      _tmp = tfd.readline()
      temperature = int(_tmp.strip())
  except (IOError, ValueError):
    temperature = 20000
  return temperature


def send_position(ais, config):
  packet = aprslib.packets.PositionReport()
  packet.fromcall = config.call
  packet.tocall = 'APRS'
  packet.symbol = config.symbol
  packet.symbol_table = config.symbol_table
  packet.timestamp = time.time()
  packet.latitude = config.latitude
  packet.longitude = config.longitude
  packet.comment = "{} - https://github.com/0x9900/aprstar".format(platform.node())
  logging.info(str(packet))
  try:
    ais.sendall(packet)
  except ConnectionError as err:
    logging.warning(err)

def send_header(ais, config):
  send_position(ais, config)
  try:
    ais.sendall("{0}>APRS::{0:9s}:PARM.Temp,Load,FreeMem".format(config.call))
    ais.sendall("{0}>APRS::{0:9s}:EQNS.0,0.001,0,0,0.001,0,0,1,0".format(config.call))
  except ConnectionError as err:
    logging.warning(err)

def ais_connect(config):
  ais = aprslib.IS(config.call, passwd=config.passcode, port=DEFAULT_PORT)
  for retry in range(5):
    try:
      ais.connect()
    except ConnectionError as err:
      logging.warning(err)
      time.sleep(10)
    else:
      return ais
  logging.error('Connection error exiting')
  sys.exit(os.EX_NOHOST)

def main():
  config = Config()
  ais = ais_connect(config)

  send_header(ais, config)
  for sequence in Sequence():
    if sequence % 10 == 1:
      send_header(ais, config)
    temp = get_temp()
    load = get_load()
    freemem = get_freemem()
    data = "{}>APRS:T#{:03d},{:d},{:d},{:d},0,0,00000000".format(
        config.call, sequence, temp, load, freemem)
    ais.sendall(data)
    logging.info(data)
    time.sleep(config.sleep)


if __name__ == "__main__":
  try:
    main()
  except KeyboardInterrupt:
    sys.exit()
