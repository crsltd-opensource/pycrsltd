"""Some classes to support import of data files
"""

from pycrsltd import bits
import sys, os, time
from psychopy import logging, visual
logging.console.setLevel(logging.DEBUG)

def test_BitsSharp():
    #set up a window
    win = visual.Window([1024,768], fullscr=True,
        screen=0, #assuming bitsSharp is connected to a secondary monitor
        useFBO=True) #useFBO needs turning on manually (in future that may be the default)
    gabor = visual.GratingStim(win,tex="sin",mask="gauss",texRes=256,
               size=[1.0,1.0], sf=[4,0], ori = 0, name='gabor1')
    gabor.setAutoDraw(True)
    
    #connect to the bits box
    if sys.platform=='win32':
        portname='COM7'
    else:
        portname=None
    bitsBox = bits.BitsSharp(portname, win=win, mode='mono++')
    assert bitsBox.OK == True
    print bitsBox.getInfo()
    
    #flip window
    for n in range(100):
        gabor.draw()
        win.flip()
#    ##status screen is slow
#    bitsBox.showStatusScreen()
#    time.sleep(2)#time to switch
#    ##get video line implicitly uses status screen
#    print bitsBox.getVideoLine(lineN=50, nPixels=5)
#    time.sleep(1)
#    #bitsBox.startMassStorageMode() #if you test this you have to repower the box after
#
#    bitsBox.startColorPlusPlusMode()
#    time.sleep(5)
#    bitsBox.startMonoPlusPlusMode()
#    time.sleep(1)
#    bitsBox.startBitsPlusPlusMode()
#    time.sleep(1)
#    bitsBox.beep(freq=800, dur=1) #at one point dur was rounded down to 0 if less than 1

if __name__ == '__main__':
    test_BitsSharp()