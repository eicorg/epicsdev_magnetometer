"""PVAccess server for Lakeshore 421 Gaussmeter."""
# pylint: disable=invalid-name
__version__ = 'v0.0.4 2026-04-30'# Probe type decoded, added instrCmdS/R PVs

import sys
import time
import argparse
from threading import Lock
from pyvisa import VisaIOError, ResourceManager, constants as visa_constants
from epicsdev import epicsdev as edev

#``````````````````PVs defined here```````````````````````````````````````````
def myPVDefs():
    """PV definitions for Lakeshore 421 Gaussmeter."""
    F, SET, U = 'features', 'setter', 'units'
    pvDefs = [
# Instrument identification
['idn',         'Instrument identification (*IDN?)', ''],
['probeType',   'Probe type (TYPE?)', ''],

# Measurement PVs
['field',       'Current magnetic field reading (FIELD?)', 0., {U:'G'}],

# Configuration PVs
#['unit',        'Measurement unit: G=Gauss, T=Tesla, O=Oersted, A=A/m',
#    ['G', 'T', 'O', 'A'],
#    {F:'WD', SET:set_unit}],
['acdc',        'Measurement mode: DC or AC',
    ['DC', 'AC'],
    {F:'WD', SET:set_acdc}],
['autoRange',   'Auto-range: 0=Off, 1=On',
    ['Off', 'On'],
    {F:'WD', SET:set_autoRange}],

# Alarm PVs
['alarmEnable', 'Alarm enable: 0=Off, 1=On',
    ['Off', 'On'],
    {F:'WD', SET:set_alarm}],
['alarmHigh',   'Alarm high setpoint', 0., {F:'W', SET:set_alarm}],
['alarmLow',    'Alarm low setpoint',  0., {F:'W', SET:set_alarm}],

# Direct command interface
['instrCmdS',   'Direct SCPI command to the instrument', '*IDN?',
    {F:'W', SET:set_instrCmdS}],
['instrCmdR',   'Response to instrCmdS', ''],
    ]
    return pvDefs
#,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
#``````````````````Constants``````````````````````````````````````````````````
Threadlock = Lock()
OK = 0
NotOK = -1

class C_():
    """Namespace for module properties"""
    dev = None  # pyvisa MessageBasedResource handle
    rm = None   # pyvisa ResourceManager


#``````````````````Device communication```````````````````````````````````````
def devCmd(cmd):
    """Send a command to the Lakeshore 421 and return the reply (if any)."""
    edev.printv(f'>devCmd: {cmd}')
    reply = None
    try:
        with Threadlock:
            if '?' in cmd:
                reply = C_.dev.query(cmd).strip()
            else:
                C_.dev.write(cmd)
    except VisaIOError:
        handle_exception(f'in devCmd({cmd})')
    return reply


def handle_exception(where):
    """Handle a VISA communication exception."""
    exceptionText = str(sys.exc_info()[1])
    msg = f'ERR: {exceptionText}: {where}'
    edev.printe(msg)
    return NotOK


#``````````````````Setters````````````````````````````````````````````````````
def set_instrCmdS(cmd, *_):
    """Setter for the instrCmdS PV: send a raw SCPI command."""
    edev.publish('instrCmdR', '')
    reply = devCmd(cmd)
    if reply is not None:
        edev.publish('instrCmdR', reply)
    edev.publish('instrCmdS', cmd)

def set_acdc(value, *_):
    """Setter for the acdc PV. Sends ACDC <0|1> command."""
    index = ['DC', 'AC'].index(str(value))
    devCmd(f'ACDC {index}')
    edev.publish('acdc', value)

def set_autoRange(value, *_):
    """Setter for the autoRange PV. Sends AUTO <0|1> command."""
    index = ['Off', 'On'].index(str(value))
    devCmd(f'AUTO {index}')
    edev.publish('autoRange', value)

def set_alarm(value, pv, *_):
    """Setter for alarmEnable, alarmHigh, alarmLow PVs.
    Re-sends the full ALARM command with current values after any change.
    Command syntax: ALARM <status>,<high>,<low>
    """
    pvname = pv.name
    edev.publish(pvname, value)
    status = ['Off', 'On'].index(str(edev.pvv('alarmEnable')))
    high   = float(edev.pvv('alarmHigh'))
    low    = float(edev.pvv('alarmLow'))
    devCmd(f'ALARM {status},{high},{low}')

#``````````````````Initialisation`````````````````````````````````````````````
def serverStateChanged(newState: str):
    """Called when the server state changes."""
    if newState == 'Start':
        edev.printi('serverStateChanged: Start')
        adopt_device_settings()
    elif newState == 'Stop':
        edev.printi('serverStateChanged: Stop')

def adopt_device_settings():
    """Read current device settings and update PVs."""
    edev.printi('adopt_device_settings')

    idn = devCmd('*IDN?')
    if idn:
        edev.publish('idn', idn)

    probe = devCmd('TYPE?')
    if probe:
        edev.publish('probeType', {'0':'HSE','1':'HST','2':'UHS'}.get(probe.strip(), probe))

    # Read ACDC setting
    acdc_reply = devCmd('ACDC?')
    if acdc_reply is not None:
        try:
            idx = int(acdc_reply.strip())
            edev.publish('acdc', ['DC', 'AC'][idx])
        except (ValueError, IndexError):
            pass

    # Read auto-range setting
    auto_reply = devCmd('AUTO?')
    if auto_reply is not None:
        try:
            idx = int(auto_reply.strip())
            edev.publish('autoRange', ['Off', 'On'][idx])
        except (ValueError, IndexError):
            pass

    # Read alarm settings: ALARM? returns <status>,<high>,<low>
    alarm_reply = devCmd('ALARM?')
    if alarm_reply:
        parts = alarm_reply.split(',')
        if len(parts) >= 3:
            try:
                edev.publish('alarmEnable', ['Off', 'On'][int(parts[0].strip())])
                edev.publish('alarmHigh', float(parts[1].strip()))
                edev.publish('alarmLow',  float(parts[2].strip()))
            except (ValueError, IndexError):
                pass

def init_visa():
    """Initialise the VISA interface to the Lakeshore 421."""
    resource = pargs.port
    baud = pargs.baud
    timeout_s = pargs.timeout
    edev.printi(f'Opening VISA resource {resource}')
    try:
        C_.rm = ResourceManager()

        open_kwargs = {
            'timeout': int(timeout_s * 1000),
            'read_termination': '\r\n',
            'write_termination': '\r\n',
        }
        if not resource.upper().startswith('TCPIP'):
            open_kwargs.update({
                'baud_rate': baud,
                'data_bits': 7,
                'parity': visa_constants.Parity.odd,
                'stop_bits': visa_constants.StopBits.one,
            })

        C_.dev = C_.rm.open_resource(resource, **open_kwargs)
    except Exception as exc:
        edev.printe(f'Could not open VISA resource {resource}: {exc}')
        sys.exit(1)

    # Clear stale instrument state/data if supported.
    try:
        C_.dev.clear()
    except Exception:
        pass

    # Verify the device responds
    idn = devCmd('*IDN?')
    if not idn:
        edev.printe('Device did not respond to *IDN?. Check connection.')
        sys.exit(1)
    edev.printi(f'IDN: {idn}')
    if 'LAKESHORE' not in idn.upper() and '421' not in idn:
        edev.printw(f'Unexpected IDN response: {idn}')

    # Set units to Gauss for consistency
    devCmd('UNIT G')

def init():
    """Module initialisation: open VISA resource and validate device."""
    init_visa()

#``````````````````Polling````````````````````````````````````````````````````
def poll():
    """Read current field and memorised peak field, publish to PVs."""
    field_reply = devCmd('FIELD?')
    field_mult = devCmd('FIELDM?')
    if field_reply is not None:
        edev.printvv(f'FIELD? reply: {field_reply}, FIELDM? reply: {field_mult}')
        multiplier = {'m':1e-3, 'k':1e3, 'M':1e6}.get(field_mult.strip(), 1)
        v = float(field_reply.strip()) * multiplier
        edev.printv(f'Parsed field value: {v} G')
        try:
            edev.publish('field', v)
        except ValueError:
            edev.printw(f'Unexpected FIELD? reply: {field_reply}')

#``````````````````Main```````````````````````````````````````````````````````
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog=__version__,
    )
    parser.add_argument('-a', '--autosave', nargs='?', default='', help=
        'Autosave control. If not given, autosave is enabled with a default '
        'file name /tmp/<device><index>.cache. '
        'If given without argument, autosave is disabled. '
        'If a file name is given, it is used for autosave.')
    parser.add_argument('-c', '--recall', action='store_false', help=
        'Do not load initial values from the pvCache file.')
    parser.add_argument('-d', '--device', default='mag421_', help=
        'Device name; the PV prefix will be <device><index>:')
    parser.add_argument('-i', '--index', default='0', help=
        'Device index; the PV prefix will be <device><index>:')
    parser.add_argument('-p', '--port', default='ASRL/dev/ttyS0::INSTR', help=
        'VISA resource string. Examples: ASRL/dev/ttyUSB0::INSTR, '
        'TCPIP::130.199.85.154::2001::SOCKET')
    parser.add_argument('-b', '--baud', type=int, default=9600, help=
        'Serial baud rate')
    parser.add_argument('-t', '--timeout', type=float, default=2.0, help=
        'Serial read timeout in seconds')
    parser.add_argument('--putlogPV', default=None, help=
        'Name of the PV where put operations are logged.')
    parser.add_argument('-v', '--verbose', action='count', default=0, help=
        'Show more log messages (-vv: show even more)')
    pargs = parser.parse_args()
    print(f'pargs: {pargs}')

    # Initialise epicsdev and create PVs
    pargs.prefix = f'{pargs.device}{pargs.index}:'
    pvDefs = myPVDefs()
    PVs = edev.init_epicsdev(
        pargs.prefix, pvDefs, pargs.verbose,
        serverStateChanged, None, pargs.autosave, pargs.recall,
        pargs.putlogPV,
    )

    # Open VISA resource and verify device
    init()

    # Start the server
    edev.set_server('Start')

    # Main loop
    server = edev.Server(providers=[PVs])
    edev.printi(
        f'Server for {pargs.prefix} started. '
        f'Sleeping per cycle: {repr(edev.pvv("sleep"))} S.'
    )
    while True:
        state = edev.serverState()
        if state.startswith('Exit'):
            break
        if not state.startswith('Stop'):
            poll()
        edev.sleep()
    edev.printi('Server exited')
