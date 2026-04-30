"""Pypet page for epicdev.epicsdev_magnetometer.
"""
# pylint: disable=invalid-name
__version__ = 'v0.1.0 2026-01-31'#

import os

#``````````````````Definitions````````````````````````````````````````````````
# python expressions and functions, used in the spreadsheet
_ = ''
def span(x,y=1): return {'span':[x,y]}
def color(*v): return {'color':v[0]} if len(v)==1 else {'color':list(v)}
def font(size): return {'font':['Arial',size]}
def just(i): return {'justify':{0:'left',1:'center',2:'right'}[i]}
def slider(minValue,maxValue):
    """Definition of the GUI element: horizontal slider with flexible range"""
    return {'widget':'hslider','opLimits':[minValue,maxValue],'span':[2,1]}

LargeFont = {'color':'light gray', **font(18), 'fgColor':'dark green'}
ButtonFont = {'font':['Open Sans Extrabold',14]}# Comic Sans MS
LYRow = {'ATTRIBUTES':{'color':'light yellow', 'font':['Arial',12], 'justify':'center'}}
lColor = color('lightGreen')
PyPath = 'python -m'

Instance = 'mag421_0:'

#``````````````````PyPage Object``````````````````````````````````````````````
class PyPage():
    def __init__(self, instance=None,
            title="epicsdev", channels=1):
        """instance: unique name of the page.
        For EPICS it is usually device prefix 
        """
        if instance is None:
            instance = Instance
        print(f'Instantiating Page {instance,title} with {channels} channels')

        #``````````Mandatory class members starts here````````````````````````
        self.namespace = 'PVA'
        self.title = instance[:-1]

        #``````````Page attributes, optional`````````````````````````
        self.page = {**color(240,240,240)}
        #self.page['editable'] = False

        #``````````Definition of columns`````````````````````````````
        self.columns = {
            1: {'width': 120, 'justify': 'right'},
            2: {'width': 80},
            3: {'width': 80, 'justify': 'right'},
            4: {'width': 80},
            5: {'width': 80, 'justify': 'right'},
            6: {'width': 80},
            7: {'width': 80},
            8: {'width': 80},
            9: {'width': 80},
        }
        """`````````````````Configuration of rows`````````````````````````````
A row is a list of comma-separated cell definitions.
The cell definition is one of the following: 
  1)string, 2)device:parameters, 3)dictionary.
The dictionary is used when the cell requires extra features like color, width,
description etc. The dictionary is single-entry {key:value}, where the key is a 
string or device:parameter and the value is dictionary of the features.
        """
        D = instance

        #``````````Abbreviations, used in cell definitions
        #``````````mandatory member```````````````````````````````````````````
        self.rows = [
['Device:',D, D+'server', D+'VERSION', 'host:',D+'HOSTNAME',D+'CPU_LOAD'],
['Status:', {D+'status': span(8,1)}],
['Cycle time:',D+'cycleTime', 'Sleep:',D+'sleep', 'Cycle:',D+'cycle'],
['Model:',{D+'idn': span(2,1)},_, 'Probe:',D+'probeType'],
[LYRow,{'Readings':span(8,1)}],
['Field:',D+'field'],#, 'Alarm:',D+'alarm'],
[LYRow,{'Settings':span(8,1)}],
#['AC/DC:', D+'acdc', 'autoRange:', D+'autoRange', 'Range:', D+'range'],
['instrCmd:',D+'instrCmdS', 'Reply:',{D+'instrCmdR': span(4,1)}],
        ]