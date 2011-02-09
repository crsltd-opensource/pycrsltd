

def testColorCAL():
    from pycrsltd import ColorCAL
    cal = ColorCAL.ColorCAL('/dev/cu.usbmodem0001', maxAttempts=5)
    assert cal.OK#connected and received 'OK00' to calibrate command
    
    mes = cal.measure()
    print 'B', mes
    assert mes[0]
    
if __name__ == "__main__":
    testColorCAL()
    print 'done'