
from pycrsltd import colorcal

try:
    from psychopy import log
    log.console.setLevel(log.DEBUG)
except:
    import logging as log
    
def testMinolta2Float():
    import numpy
    assert colorcal._minolta2float(50347)== -0.0347
    assert colorcal._minolta2float(10630)==  1.0630
    assert numpy.alltrue(colorcal._minolta2float([10635, 50631]) == numpy.array([ 1.0635, -0.0631]))
    
def testColorCAL():
    cal = colorcal.ColorCAL('/dev/cu.usbmodem0001', maxAttempts=5)
    assert cal.OK#connected and received 'OK00' to cal.getInfo()

    #get help
    helpMsg = cal.sendMessage('?')
    print 'Help info:'
    for line in helpMsg[1:]: #the 1st 3 lines are just saying OK00
        print '\t', line.rstrip().lstrip() #remove whitespace from left and right
        
    #get info
    print 'Info:'
    ok, ser, firm, firmBuild= cal.getInfo()
    print 'INFO: ok=True serial#=%s firmware=%s_%s' %(ser,firm,firmBuild)
    assert ok#make sure that the first value returned was True
    
    ok = cal.calibrateZero()
    assert ok
    
    #take a measurement
    ok, x, y, z = cal.measure()
    print 'MES: ok=%s (%.2f, %.2f, %.2f)' %(ok, x, y, z)
    assert ok#make sure that the first value returned was True
    print 'calibZeroSuccess=', cal.calibrateZero()
    print cal.getMatrix()
    
    log.flush()
    
if __name__ == "__main__":
    testColorCAL()
    testMinolta2Float()
    print 'done'