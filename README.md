# aprstar

With this simple python program you can monitor your Allstar or
pi-star health using APRS metrics.  You can see an example of the
metrics logged by my allstar node. https://aprs.fi/telemetry/a/W6BSD-7

The metrics are temperature, CPU load average, and Available memory.

## Installation

This program can run using either python3 or python2. I have try to
limit the number of dependencies in other python package but there is
still a few that need to be installed.

The python dependencies can be installed using the command pip

```
# sudo pip install aprslib
# sudo pip install json
# sudo pip install ConfigParser
```

The module `json` and `configparser` should be already installed but I
have found some instances where they were not.


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


### Starting the service

```
# sudo systemctl enable aprstar.service
# sudo systemctl start aprstar.service
# sudo systemctl status aprstar.service
```
