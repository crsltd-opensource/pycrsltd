#!/usr/bin/env python
#coding=utf-8

# Copyright (c) Cambridge Research Systems (CRS) Ltd
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

#Acknowledgements
#    This code was written by Jon Peirce

__docformat__ = "restructuredtext en"

import time
try: import serial
except: serial=False

try: from psychopy import log
except:
    import logging as log

class ColorCAL:
    """A class to handle the CRS Ltd ColorCAL device
    """
    def __init__(self, port, maxAttempts=1):

        if not serial:
            raise ImportError('The module serial is needed to connect to photometers. ' +\
                "On most systems this can be installed with\n\t easy_install pyserial")

        if type(port) in [int, float]:
            self.portNumber = port #add one so that port 1=COM1
            self.portString = 'COM%i' %self.portNumber#add one so that port 1=COM1
        else:
            self.portString = port
            self.portNumber=None
        self.isOpen=0
        self.lastQual=0
        self.lastLum=None
        self.type='ColorCAL'
        self.com=False
        self.OK=True#until we fail
        self.maxAttempts=maxAttempts

        #try to open the port
        try:self.com = serial.Serial(self.portString)
        except:
            self._error("Couldn't connect to port %s. Is it being used by another program?" %self.portString)

        #setup the params for serial port
        if self.OK:
            self.com.close()#not sure why this helps but on win32 it does!!
#            self.com.setByteSize(7)#this is a slightly odd characteristic of the Minolta LS100
#            self.com.setBaudrate(4800)
#            self.com.setParity(serial.PARITY_EVEN)#none
#            self.com.setStopbits(serial.STOPBITS_TWO)
            try:
                self.com.open()
                self.isOpen=1
            except:
                self._error("Opened serial port %s, but couldn't connect to ColorCAL" %self.portString)

        ret = self._calibrate()
        self.OK = (ret=='OK00')

    def sendMessage(self, message, timeout=1.0):
        """Send a command to the photometer and wait an alloted
        timeout for a response.
        """
        if message[-2:]!='\n':
            message+='\n'     #append a newline if necess

        #flush the read buffer first
        prevMsg = self.com.read(self.com.inWaiting())#read as many chars as are in the buffer
        if len(prevMsg) and prevMsg not in ['>\n', '\r>']:
            log.debug('prevMsg found:', repr(prevMsg))

        retVal=''
        attemptN=0
        while len(retVal)==0 and attemptN<self.maxAttempts:
            #send the message
            self.com.write(message)
            self.com.flush()
            #get reply (within timeout limit)
            self.com.setTimeout(timeout)
            log.debug('Sent command:'+message[:-2])#send complete message
            if message in ['?\n']:
                retVal=[]
                while self.com.inWaiting():
                    retVal.append(self.com.readline())
            else:
                retVal= self.com.readline()
                while retVal.startswith('\r'): retVal=retVal[1:]
                while retVal.endswith('\n'): retVal=retVal[:-1]
        return retVal

    def measure(self):
        """Conduct a measurement and return the X,Y,Z values

        Usage::

            ok, x, y, z = colorCal.measure()

        Where:
            ok is True/False
            x, y, z are the CIE coordinates

        """
        time.sleep(0.1)
        ret = self.sendMessage('MES')
        if len(ret)==1: #we only got ['OK00']
            #the device reported OK but gave no vals. Try again.
            ret = self.sendMessage('MES')
        ret=ret.split(',')#separate into words
        ok = (ret[0]=='OK00')
        x, y, z = float(ret[1]), float(ret[2]), float(ret[3])
        return ok, x, y, z

    def _calibrate(self):
        """This should be done before any measurements are taken
        """
        return self.sendMessage("UZC")

    def _error(self, msg):
        self.OK=False
        log.error(msg)