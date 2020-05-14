#!/usr/bin/python2.7

import itertools
import json
import logging
import os
import platform
import time
import urllib

from configparser import ConfigParser
from io import StringIO

import aprslib

CONFIG_FILE = "/etc/aprstar.conf"
CONFIG_DEFAULT = u"""
[APRS]
call: W6BSD-7
latitude: 0
longitude: 0
"""

THERMAL_FILE = "/sys/class/thermal/thermal_zone0/temp"
LOADAVG_FILE = "/proc/loadavg"
DEFAULT_PORT = 14580

logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)


class Config(object):

  def __init__(self):
    parser = ConfigParser()
    parser.readfp(StringIO(CONFIG_DEFAULT))

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
    self._passcode = val


def get_coordinates():
  url = "http://ip-api.com/json/"
  try:
    response = urllib.urlopen(url)
    data = json.loads(response.read())
  except IOError as err:
    logging.error(err)
    return (0, 0)
  else:
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
  packet.symbol = '*'
  packet.timestamp = time.time()
  packet.latitude = config.latitude
  packet.longitude = config.longitude
  packet.comment = platform.node()
  logging.info(str(packet))
  ais.sendall(packet)


def main():

  config = Config()

  ais = aprslib.IS(config.call, passwd=config.passcode, port=DEFAULT_PORT)
  ais.connect()
  for sequence in itertools.cycle(range(1, 100)):
    if sequence % 10 == 1:
      send_position(ais, config)
      ais.sendall("{0}>APRS::{0:9s}:PARM.Temp,Load".format(config.call))
      ais.sendall("{0}>APRS::{0:9s}:EQNS.0,0.001,0,0,0.001,0".format(config.call))
    temp = get_temp()
    load = get_load()
    data = "{}>APRS:T#{:03d},{:d},{:d},0,0,0,00000000".format(config.call, sequence, temp, load)
    ais.sendall(data)
    logging.info(data)
    time.sleep(300)


if __name__ == "__main__":
  main()
