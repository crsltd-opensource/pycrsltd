
import serial

ACK='\x06'
NACK='\x15'

class OptiCal(object):
    def __init__(self, com_port,debug=True, timeout=10):
        self.ser = serial.Serial(com_port, timeout=timeout)

    def _calibrate(self):
        self.ser.write('C')
        ret = self.ser.read()
        if ret == "":
            print "should raise excpetion since reading timed out"
        if ret == NACK:
            print "should raise excpetion due to NACK"

    def _read_eeprom(self, address):
        self.ser.write(chr(128+address))
        return self.ser.read(2)[0]

