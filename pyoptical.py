#!/usr/bin/env python

import serial

ACK='\x06'
NACK='\x15'

class OptiCal(object):
    def __init__(com_port,debug=True, timeout=10):
        self.ser = serial.Serial(com_port,timeout=timeout)
    def _calibrate(self):
        self.ser.write('C')
        ret = self.read
        if ret != ACK:
            raise RuntimException('Optical returned NACK byte')
    
