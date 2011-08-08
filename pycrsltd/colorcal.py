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
import numpy

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
        #check that we can communicate with it
        ok, ser, firm, firmBuild = self.getInfo()
        self.OK = ok

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
            log.debug('Sent command:%s (attempt %i)' %(message[:-2],attemptN))#send complete message
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

    def getInfo(self):
        """Queries the device for information

        usage::
            ok, serialNumber, firmwareVersion, firmwareBuild = colorCal.getInfo()

        `ok` will be True/False
        Other values will be a string or None.

        """
        retVal = self.sendMessage('IDR').split(',')
        ok = (retVal[0]=='OK00')
        if ok:
            firmware=retVal[2]
            serialNum=retVal[4]
            firmBuild=retVal[-1]
        else:
            firmware=0
            serialNum=0
            firmBuild=0
        return ok, serialNum, firmware, firmBuild

    def calibrateZero(self):
        """This should be done once before any measurements are taken when
        """
        val = self.sendMessage("UZC")
        if val=='OK00':
            return True
        elif val=='ER11':
            log.error("Could not calibrate ColorCAL2. Is it properly covered?")
        return 0#if we got here there was a problem, either reading or an ER11
    def getMatrix(self):

        matrix=numpy.zeros((3,3),dtype=float)
        for rowN in range(4):
            val = self.sendMessage('r0%i' %rowN)
            vals=val.split(',')#convert to list of values

            if vals[0]=='OK00' and len(vals)>1:
                #convert to numpy array
                rawVals=numpy.array(vals[1:], dtype=int)
                log.debug('row %i: x=%i, y=%i, z=%i' %(vals[0],vals[2],vals[3]))
            else:
                print 'got this from command r0%i: %s' %(rowN, repr(val))
            time.sleep(0.1)
    def _error(self, msg):
        self.OK=False
        log.error(msg)

def _minolta2Float(inVal):
    """Takes a number, or numeric array (any shape) and returns the appropriate
    float.

    minolta stores;
        +ve values as val*10000
        -ve values as -val*10000+50000

    >>> _minolta2Float(50347)#NB returns a single float
    -0.034700000000000002
    >>> _minolta2Float(10630)
    1.0630999999999999
    >>> _minolta2Float([10635, 50631])#NB returns a numpy array
    array([ 1.0635, -0.0631])

    """
    arr=numpy.asarray(inVal)#convert  to array if needed
    #handle single vals
    if arr.shape==():
        if inVal<50000: return inVal/10000.0
        else: return (-inVal+50000.0)/10000.0
    #handle arrays
    negs = (arr>50000)#find negative values
    out = arr/10000.0#these are the positive values
    out[negs] = (-arr[negs]+50000.0)/10000.0
    return out