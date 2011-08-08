

def testColorCAL():
    from pycrsltd import colorcal
    cal = colorcal.ColorCAL('/dev/cu.usbmodem0001', maxAttempts=5)
    assert cal.OK#connected and received 'OK00' to calibrate command
    #get help
    helpMsg = cal.sendMessage('?')
    print 'Info:'
    for line in helpMsg[4:]: #the 1st 3 lines are just saying OK00
        print '\t', line.rstrip().lstrip() #remove whitespace from left and right
    #take a measurement
    mes = cal.measure()
    print 'MES:', mes
#    assert mes[0]
    
if __name__ == "__main__":
    testColorCAL()
    print 'done'