# epicsdev_magnetometer
Python-based EPICS PVAccess server for various magnetometers.
It is based on [p4p](https://epics-base.github.io/p4p/) and
[epicsdev](https://github.com/ASukhanov/epicsdev) packages and can run
standalone on Linux, macOS, and Windows platforms.

## Supported devices

### Lakeshore 421 Gaussmeter

Communicates via PyVISA (RS-232 settings: 9600 baud, 7 data bits, odd parity, 1 stop bit).

#### Supported SCPI commands
| PV | SCPI command | Description |
|---|---|---|
| `field` | `FIELD?` | Current magnetic field reading |
| `fieldMax` | `FIELDM?` | Maximum/minimum memorised field |
| `alarmEnable`, `alarmHigh`, `alarmLow` | `ALARM` | Alarm configuration |
| `autoRange` | `AUTO` | Auto-range mode |
| `idn` | `*IDN?` | Instrument identification |
| `probeType` | `TYPE?` | Probe type |
| `unit` | `UNIT` | Measurement unit (G/T/O/A) |
| `acdc` | `ACDC` | AC or DC measurement mode |
| `instrCmdS` / `instrCmdR` | *any* | Direct SCPI command / response |

#### Installation
```
pip install epicsdev_magnetometer
```

#### Run
```
python -m epicsdev_magnetometer -p ASRL/dev/ttyUSB0::INSTR
```
Pass a VISA resource string, e.g. `ASRL/dev/ttyUSB0::INSTR`.
Use `-h` for the full list of options.
