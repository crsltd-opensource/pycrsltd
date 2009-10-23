#!/usr/bin/env python
#coding=utf-8

import serial

ACK='\x06'
NACK='\x15'

def to_int(list_of_bytes):
    list_of_bytes.reverse()
    return int("".join(list_of_bytes).encode('hex'),16)

def OptiCalException(Exception):
    pass

def NACKException(Exception):
    """ is raised when the OptiCal sends a NACK byte """
    def __str__(self)
        return "OptiCal sent a NACK while trying to: " self.message

def TimeoutException(Exception):
    """ is raised when the OptiCal does not respond within the timeout limit """
    def __str__(self)
        return "OptiCal timeout while trying to: " self.message

class OptiCal(object):
    """ object to access the OptiCal


    """
    def __init__(self, com_port,debug=True, timeout=10):
        self.phot = serial.Serial(com_port, timeout=timeout)
        self._calibrate()
        self._read_ref_defs()

    def _calibrate(self):
        self._send_command('C', "calibrate")

    def _set_current_mode(self):
        self._send_command('I', "set current mode")

    def _set_voltage_mode(self):
        self._send_command('V', "set voltage mode")

    def _send_command(self, command, description):
        self.phot.write(command)
        ret = self.phot.read()
        if ret == "":
            raise TimeoutException(description)
        if ret == NACK:
            raise NACKException(description)

    def _read_ref_defs(self):
        """ read all parameters with a ref definition """
        self.V_ref = to_int(self._read_eeprom(16,19))
        self.Z_count = to_int(self._read_eeprom(32,35))
        self.R_feed = to_int(self._read_eeprom(48,51))
        self.R_gain = to_int(self._read_eeprom(64,67))
        self.K_cal = to_int(self._read_eeprom(96,99))

    def _read_eeprom_single(self, address):
        """ read contents of eeprom at single address

            arguments:
                address: an integer in the range 0<i<100

            returns:
                a byte in the range 0<i<256 as str

            note: the ACK byte is removed for you
        """
        self.phot.write(chr(128+address))
        return self.phot.read(2)[0]

    def _read_eeprom(self, start, stop):
        """ read contents of eeprom between start and stop inclusive

            arguments:
                start: an integer in the range 0<i<100
                stop: and integer in the range 0<i<100

            returns:
                a list of bytes in the range 0<i<256 as str
        """
        ret = []
        for i in range(start, stop+1):
            ret.append(self._read_eeprom_single(i))
        return ret

    def _read_product_type(self):
        return self._read_eeprom(0,1)

    def _read_optical_serial_number(self):
        return self._read_eeprom(2,5)

    def _read_firmware_version(self):
        return self._read_eeprom(6,7)

    def _read_probe_serial_number(self):
        return self._read_eeprom(80,95)

    def _read_ref_voltage(self)
        return self._read_eeprom(16,19)

    def _read_zero_error(self):
        return self._read_eeprom(32,35)

    def _read_feedback_resistor(self):
        return self._read_eeprom(48,51)

    def _read_voltage_gain_resistor(self):
        return self._read_eeprom(64,67)

    def _read_probe_calibration(self):
        return self._read_eeprom(96,99)
