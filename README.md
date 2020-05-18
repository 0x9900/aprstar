# aprstar

With this simple python program you can monitor your Allstar or
pi-star health using APRS metrics.  You can see an example of the
metrics logged by my allstar node. https://aprs.fi/telemetry/a/W6BSD-7

The metrics are temperature, CPU load average, and Available memory.

## Installation (Pi-Star)

This program can run using either python3 or python2. As of today, the
hamvoip allstar image, uses an older version of Linux and the default
python is 2.7, this is why this program uses python 2.7.

I have try to limit the number of dependencies in other python package
but there is still a few that need to be installed.

The following instructions for installing `aprstar` on Pi-Star.

On the Pi-Star image a very minimal version of python has been
installed make sure the main python libraries are installed by running
the following commands.

```
# sudo apt update
# sudo apt install python-pip -y
```

The following packages are the 2 dependencies used by `aprstar`. They
can be installed using the command pip.

```
# sudo pip install ConfigParser
# sudo pip install aprslib
```

The module `configparser` should be already installed but I have found
some instances where it is not.

### Installing aprstar.py

```
# sudo cp aprstar.py /usr/local/bin/aprstar
# sudo chmod a+x /usr/local/bin/aprstar
```

### Installing the aprstar service

```
# sudo cp aprstar.service /lib/systemd/system/aprstar.service
# sudo chmod 0644 /lib/systemd/system/aprstar.service
```

## Configurations

Create the file `/etc/aprstar.conf`, using your favorite editor. For example:

```
# sudo nano /etc/aprstar.conf
```

And add the following lines, replacing `N0CALL` with your call
sign. The `1` is the id of your device. If you have several device,
replace the 1 by your device number.

```
[APRS]
call: N0CALL-1
```

Use Ctrl-X to save and exit.

This is the minimal configuration. You can also add the keywords
`longitude` and `latitude`, with the lat, lon in decimal form. If you
don't indicate the position the program will use the ip-address to
determine where you are.

## Starting the service

```
# sudo systemctl enable aprstar.service
# sudo systemctl start aprstar.service
```

You can now run the status command to see if everything is running
smoothly and you have no errors.

```
# sudo systemctl status aprstar.service
```
