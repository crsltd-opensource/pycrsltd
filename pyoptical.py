#!/usr/bin/env python
#coding=utf-8

""" pyoptical - a pure python interface to the CRS 'OptiCal' photometer

    @author:  Valentin Haenel <valentin.haenel@gmx.de>
    @version: 0.1

    This module provides the 'OptiCal' class and some supporting code.

"""

import serial

ACK='\x06'
NACK='\x15'

def to_int(list_of_bytes):
    """ convert a list of bytes(in least significant byte order) to int """
    list_of_bytes.reverse()
    return int("".join(list_of_bytes).encode('hex'),16)

class OptiCalException(Exception):
    """ base exception for all OptiCal exceptions """

class NACKException(OptiCalException):
    """ is raised when the OptiCal sends a NACK byte to signify an error"""
    def __str__(self):
        return "OptiCal sent a NACK while trying to: %s" % self.message

class TimeoutException(OptiCalException):
    """ is raised when the OptiCal does not respond within the timeout limit """
    def __str__(self):
        return "OptiCal timeout while trying to: %s" % self.message

class OptiCal(object):
    """ object to access the OptiCal

        Example:

        import pyoptical
        op = pyoptical.OptiCal('dev/dev/ttyUSB0')
        try:
            op.read_luminance()
            op.read_voltage()
        except pyoptical.NACKException as e:
            print e

        Notes about the com_port:
            The com_port argument for the constructor may vary depending on both
            your operating system and how you connect to the OptiCal. This code was
            developed using a usb-to-serial adapter that contains a PL2303 chipset
            manufactured by Prolific:
            http://www.prolific.com.tw/eng/Products.asp?ID=59. The following
            sections outine how to access the OptiCal using pyoptical and a
            usb-to-serial adapter containing the prolific chipset. We have not tried
            this code using a raw serial port, but would be very interested to hear
            from you if you do.

            Linux (Ubuntu Hardy):
                Support for the PL2303 chipset is compiled into the kernel, and the device
                is automatically recognised. You could check 'dmesg' for the
                following output:

                usb 2-1: new full speed USB device using uhci_hcd and address 4
                usb 2-1: configuration #1 chosen from 1 choice
                pl2303 2-1:1.0: pl2303 converter detected
                usb 2-1: pl2303 converter now attached to ttyUSB0

                In this case the com_port string is simply '/dev/ttyUSB0'

            Mac OSX (10.5.8 Leopard)
                Support for the PL2303 chipset is provided by the following
                open source driver:
                http://osx-pl2303.sourceforge.net/
                In this case the com_port string would be something along the
                lines of '/dev/tty.PL2303-xxx', for example:
                '/dev/tty.PL2303-000031FD'

            Other Operating Systems and Adapters:

                This code has two limitations, most importantly pyserial must support
                your platform. Secondly, if you wish to use a usb-to-serial
                adapter a driver for your target operating system must be
                available from the manufacturer or possibly a third party (for
                exampl and open source driver).

        Notes about possible exceptions:
            There are three types of exceptions that can happen:
                OptiCalException
                NACKException
                TimeoutException

            The OptiCalException is the base class for all exceptions in this
            module, and it is used as a general purpose exception to signify
            errors on the part of the programmer, do not quietly except these.

            The NACKException is raised when the OptiCal responds with a NACK
            byte. It does this either if the command was not understood or if
            the command failed. If this happens during initialization, you may
            have to re-initialise the device. If this happens during readout it
            should be safe to try again instead of terminating the program.

            The TimeoutException is raised when no answer is received within the
            default timeout length. This might be caused by a number of issues,
            but essentially means that somehow the communication with the
            OptiCal might be interrupted, for example because it is no longer
            connected to the computer.

        Implementation details:

            The interface is implemented according to the protocol specification in the
            OptiCal-User-Guide Version 4, 1995 including the following ammendments:
                a) To read out the ADC value, an 'L' must be sent instead of an 'R'
                b) The equations to convert from ADC to meaningful units had changed. See
                read_luminance() and read_voltage() for details.

            The constructor will first perform the initial calibration of the
            device as required by the protocol specification. Next it will read
            out the so called 'reference parameters' and store them as private
            variables. (The reference parameters are listed in the protocol
            specification and are used to convert the raw ADC reading into
            meaningful units when either one of the 'read_*()' methods is
            called.) Lastly it will put the device into the default mode.

            The OptiCal supports two readout modes 'current' and 'voltage', and
            the constructor uses 'current' mode by default. In 'current' mode we
            can read luminance and in 'voltage' mode we can read voltage.
            When using either of the 'read_luminance()' and 'read_voltage()'
            methods, the OptiCal is put into the correct mode in case it is not. 

    """

    def __init__(self, com_port, timeout=5):
        """ initialise OptiCal

            arguments:
                com_port:   name of the com_port
                timeout:    time in seconds to wait for a response

            For more information about the 'com_port' and 'mode' arguments see
            the docstring of the class.

        """
        self._phot = serial.Serial(com_port, timeout=timeout)
        self._calibrate()
        self._read_ref_defs()
        self._read_other_defs()
        self._set_current_mode()

    def __str__(self):
        return "Optical found at : " + self._phot.port + "\n" + \
               "Product Type :     " + self._product_type + "\n" \
               "Optical S/N  :     " + str(self._optical_serial_number) + "\n" \
               "Firmware version : " + self._firmware_version + "\n" \
               "V_ref:             " + str(self._V_ref) + "\n" + \
               "Z_count:           " + str(self._Z_count) + "\n" + \
               "R_feed:            " + str(self._R_feed) + "\n" + \
               "R_gain:            " + str(self._R_gain) + "\n" + \
               "Probe S/N          " + str(self._probe_serial_number) + "\n" + \
               "K_cal:             " + str(self._K_cal) + "\n"


    def _calibrate(self):
        """ perform initial calibration

            As stated in the OptiCal user guide, this must be done after
            powering up the device, before any readouts are performed.

        """
        self._send_command('C', "calibrate")

    def _set_current_mode(self):
        """ put the device into 'current' mode """
        self._mode = 'current'
        self._send_command('I', "set current mode")

    def _set_voltage_mode(self):
        """ put the device into 'voltage' mode """
        self._mode = 'voltage'
        self._send_command('V', "set voltage mode")

    def _send_command(self, command, description):
        """ send a single command charecter and read a single response (ACK/NACK)"""
        self._phot.write(command)
        ret = self._phot.read()
        self._check_return(ret, description)

    def _check_return(self, ret, description):
        """ check the return value of a read, raise exception if its not o.k. """
        if ret == "":
           raise TimeoutException(description)
        if NACK in ret:
           raise NACKException(description)

    def _read_ref_defs(self):
        """ read all parameters with a ref definition """
        self._V_ref = self._read_V_ref()
        self._Z_count = self._read_Z_count()
        self._R_feed = self._read_R_feed()
        self._R_gain = self._read_R_gain()
        self._K_cal = self._read_K_cal()

    def _read_other_defs(self):
        """ read all parameters that do not have a ref definition """
        self._product_type = self._read_product_type()
        self._optical_serial_number = self._read_optical_serial_number()
        self._firmware_version = self._read_firmware_version()
        self._probe_serial_number = self._read_probe_serial_number()

    def _read_eeprom_single(self, address):
        """ read contents of eeprom at single address

            arguments:
                address: an integer in the range 0<i<100

            returns:
                a byte in the range 0<i<256 as str

            note: the ACK byte is truncated
        """
        self._phot.write(chr(128+address))
        ret = self._phot.read(2)
        self._check_return(ret, "reading eeprom at address %d" % address)
        # if _check_return does not raise an excpetion
        return ret[0]

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

    def _read_adc(self):
        """ read and adjust the ADC value """
        self._phot.write('L')
        ret = self._phot.read(4)
        self._check_return(ret, "reading adc value")
        # truncate the ACK
        ret = ret[:-1]
        # obtain an integer value from the bytes
        adc = to_int([ret[0], ret[1], ret[2]])
        return adc - self._Z_count - 524288

    def read_luminance(self):
        """ the luminance measured in cd/m**2 """
        if self._mode is not 'current':
            self._set_current_mode()
        ADC_adjust = self._read_adc()
        numerator =  (float((ADC_adjust)/524288.0) * self._V_ref * 1.e-6)
        denominator = self._R_feed * self._K_cal * 1.e-15
        return max(0.0,numerator / denominator)

    def get_voltage(self):
        """ the measured voltage in V """
        if self._mode is not 'voltage':
            self._set_voltage_mode()
        return self._get_measurement()

    def _read_product_type(self):
        return str(self._read_eeprom(0,1))

    def _read_optical_serial_number(self):
        return to_int(self._read_eeprom(2,5))

    def _read_firmware_version(self):
        return str(self._read_eeprom(6,7))

    def _read_probe_serial_number(self):
        return int("".join(self._read_eeprom(80,95)))

    def _read_V_ref(self):
        """ reference voltage in microV """
        return to_int(self._read_eeprom(16,19))

    def _read_Z_count(self):
        """ zero error in ADC counts """
        return to_int(self._read_eeprom(32,35))

    def _read_R_feed(self):
        """ feedback resistor in Ohm """
        return to_int(self._read_eeprom(48,51))

    def _read_R_gain(self):
        """ voltage gain resistor in Ohm """
        return to_int(self._read_eeprom(64,67))

    def _read_K_cal(self):
        """ probe calibration in fA/cd/m**2 """
        return to_int(self._read_eeprom(96,99))
