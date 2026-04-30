# epicsdev_magnetometer. Alpha release 0.0.3
Python-based EPICS PVAccess server for various magnetometers.
It is based on [p4p](https://epics-base.github.io/p4p/) and
[epicsdev](https://github.com/ASukhanov/epicsdev) packages and can run
standalone on Linux, macOS, and Windows platforms.

## Supported devices

### Lakeshore 421 Gaussmeter

Communicates via PyVISA (RS-232 settings: 9600 baud, 7 data bits, odd parity, 1 stop bit).

#### Installation
```
pip install epicsdev_magnetometer
```

#### Run
```
# connecting with USB-RS232 adapter
python -m epicsdev_magnetometer.lakeshore -p ASRL/dev/ttyUSB0::INSTR
# or connecting through DIGI:
python -m epicsdev_magnetometer.lakeshore -p TCPIP::130.199.85.154::2001::SOCKET
```
Use `-h` for the full list of options.
