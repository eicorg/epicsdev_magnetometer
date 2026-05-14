"""Scan the magnetometer field as a function of position and coil currents.
"""
# pylint: disable=invalid-name
___version__ = 'v0.0.1 2026-05-13'#
import time
from time import perf_counter as timer
from threading import Event
import csv
import argparse
import numpy as np
from p4p.client.thread import Context

IFace = Context('pva')
EventScan = Event()
EventExit = Event()
Scan,Stop = 2,3# Workaround: hardcoded index of Scan and Stop choice of magnetometer PV 'measure'
SleepTime = 0.# time to wait for the measurement to complete; adjust as needed

class C_():# mutable variables
    magnetometer = 'mag421_0:'# PV prefix for the magnetometer; the position PV will be <magnetometer>position, the field PV will be <magnetometer>field, etc.
    setPoints = {
        # Setpoint PVs of the coils: PV name, min, max, step, unit
        'LCC': ['oppis_magf:coil_out_sp', 0., 130.0, 2.0, 'A'],
        'ICC1': ['oppis_magf:coil_in1_sp', 0., 1.4, 0.1, 'A'],
        'ICC2': ['oppis_magf:coil_in2_sp', 0., 3.0, 0.2, 'A'],
    }
    measure = ''# current measurement mode, read from the magnetometer PV 'measure'
    writer = None# CSV writer object for logging the results; set in the main block after opening the file
    subscription = None# PV subscription object for the 'measure' PV; set in the main block after creating the subscription
    steps = 0

def _printTime():
    return time.strftime("%m%d:%H%M%S")
def printi(msg):
    """Print info message"""
    print(f'inf_@{_printTime()}: {msg}')
def printw(msg):
    """Print warning message"""
    print(f'WAR_@{_printTime()}: {msg}')
def printe(msg):
    """Print error message"""
    print(f'ERR_{_printTime()}: {msg}')

def setPointRange(key):
    """Return the range of set points for the given key."""
    return np.arange(C_.setPoints[key][1], C_.setPoints[key][2], C_.setPoints[key][3]) 

def callback_measure(value):
    """Callback function for changes in the 'measure' PV.
    Update the measurement mode and signal the scan event if the mode is set to Scan. 
    If the mode is set to Stop, signal both the scan and exit events.
    """
    C_.measure = int(value)
    #print(f'>cb {type(value)} {C_.measure} {str(value)}')
    if C_.measure == Stop:
        printi('Measurement mode set to Stop')
        EventExit.set() # signal exit
        EventScan.set() # exit the loop
    EventScan.set()

perf={'total':0., 'coil':0., 'field':0., 'update':0.}# times for performance monitoring
def session():
    """Main loop: wait for the scan event, then loop through all set points and read the field."""
    C_.steps = 0
    perf['total'] = timer()
    while EventScan.wait():
        if EventExit.is_set():
            return f'Exit is signalled after {C_.steps} steps'
        EventScan.clear()
        if C_.measure == Stop:
            return (f'Measurement mode changed to Stop')
        if C_.measure != Scan:
            printw(f'Measurement mode is {C_.measure}, waiting for Scan')
            continue
        pos = IFace.get(C_.magnetometer+'position')
        printi(f'Scan for position {pos}')
        for lcc in setPointRange('LCC'):
            ts = timer()
            IFace.put(C_.setPoints['LCC'][0], lcc)
            perf['coil'] += timer() - ts
            for icc1 in setPointRange('ICC1'):
                ts = timer()
                IFace.put(C_.setPoints['ICC1'][0], icc1)
                perf['coil'] += timer() - ts
                for icc2 in setPointRange('ICC2'):
                    if EventExit.is_set():
                        return f'Exit is signalled after {C_.steps} steps'
                    ts = timer()
                    IFace.put(C_.setPoints['ICC2'][0], icc2)
                    perf['coil'] += timer() - ts
                    ts = timer()
                    IFace.put(C_.magnetometer+'update', C_.steps) # trigger measurement
                    perf['update'] += timer() - ts
                    C_.steps += 1
                    time.sleep(SleepTime) # wait for the measurement to complete
                    ts = timer()
                    field = IFace.get(C_.magnetometer+'field')
                    perf['field'] += timer() - ts
                    C_.writer.writerow([f'{pos:.5g}', f'{lcc:.5g}', f'{icc1:.5g}', f'{icc2:.5g}', f'{field:.5g}'])
        printi(f'Recorded {C_.steps} points. You can change position and scan again')
    return f'Session completed with {C_.steps} steps'

def finish_all():
    """Set all solenoids to 0 and close PV subscription."""
    C_.subscription.close()
    print('Setting all solenoids to 0.')
    IFace.put(C_.setPoints['LCC'][0], 0.)
    IFace.put(C_.setPoints['ICC1'][0], 0.)
    IFace.put(C_.setPoints['ICC2'][0], 0.)
    IFace.put(C_.magnetometer+'measure', 'OneShot') # reset measurement mode

if __name__ == "__main__":
    """Main entry point: set up CSV file and start the session."""

    # Issue Stop command to exit other sessions and ensure we start in a known state
    IFace.put(C_.magnetometer+'measure', 'Stop')
    time.sleep(0.1) # wait for the Stop command to take effect
    IFace.put(C_.magnetometer+'measure', 'OneShot') # reset measurement mode to OneShot

    # Create subscription to the 'measure' PV to monitor changes in measurement mode
    C_.subscription = IFace.monitor(C_.magnetometer+'measure', callback_measure)
    print('Please change position and set Measurement to Scan.')

    # Wait for the scan event to be triggered by the callback when the user sets the measurement mode to Scan.
    EventScan.clear()
    EventScan.wait()

    # Open CSV file for logging; filename includes timestamp for uniqueness
    fname = time.strftime('magsan_%Y%m%d_%H%M.csv')

    # Write header and start session
    with open(fname, 'w', newline='') as csvfile:
        C_.writer = csv.writer(csvfile)
        C_.writer = csv.writer(csvfile)
        C_.writer.writerow(['Position (cm)', 'LCC (A)', 'ICC1 (A)', 'ICC2 (A)', 'Field (G)'])

        # Scan session
        result = session()

        # Scan completed or exit signalled; calculate performance metrics
        perf['total'] = (timer() - perf['total'])
        if C_.steps > 0:
            for key in perf:
                perf[key] = round(perf[key]/C_.steps*1000, 1)
            printi(f'Performance (ms/step): {perf}')

        # Print final result
        printi(result)
        C_.writer.writerow([f'#{result}'])
    
    finish_all()
