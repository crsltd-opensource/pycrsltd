"""Some classes to support import of data files
"""

from pycrsltd import bits
import sys, os
from psychopy import logging
logging.console.setLevel(logging.DEBUG)

thisDir = os.path.split(__file__)[0]

def test_BitsSharp():
    if sys.platform=='win32':
        portname='COM7'
    else:
        portname=None
    box = bits.BitsSharp(portname)
    assert box.OK == True
    print box.getInfo()
    #box.startMassStorageMode() #if you test this you have to repower the box
    box.beep() #don't hear anything!?
    
if __name__ == '__main__':
    test_BitsSharp()