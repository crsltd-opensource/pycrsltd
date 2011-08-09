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

eol = "\n\r"#unusual for a serial port?!

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
        self.lastLum=None
        self.lastCmd=''
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
        self.ok, self.serialNum, self.firm, self.firmBuild = self.getInfo()
        self.calibMatrix=self.getCalibMatrix()

    def sendMessage(self, message, timeout=0.1):
        """Send a command to the photometer and wait an alloted
        timeout for a response.
        """

        #flush the read buffer first
        prevOut = self.com.read(self.com.inWaiting())#read as many chars as are in the buffer
        if len(prevOut) and prevOut not in ['>'+eol, eol]:
            #do not use log messages here
            print 'Resp found to prev cmd (%s):%s' %(self.lastCmd, prevOut)
        self.lastCmd=message

        if message[-2:] not in ['\n', '\n\r']:
            message+='\n'     #append a newline if necess
        #send the message
        self.com.write(message)
        self.com.flush()
        #get reply (within timeout limit)
        self.com.setTimeout(timeout)
        log.debug('Sent command:%s' %(message[:-1]))#send complete message

        #get output lines using self.readlin, not self.com.readline
        #colorcal signals the end of a message by giving a command prompt
        lines=[]
        thisLine=''
        nEmpty=0
        while (thisLine != '>') and (nEmpty<=self.maxAttempts):
            #self.com.readline can't handle custom eol
            thisLine=self.readline(eol=eol)
            if thisLine in [eol, '>', '']:#lines we don't care about
                nEmpty+=1
                continue
            else:
                lines.append(thisLine.rstrip(eol))#line without any eol chars
                nEmpty=0

        #got all lines and reached '>'
        if len(lines)==1:
            return lines[0]#return the string
        else:
            return lines#a list of lines

    def measure(self):
        """Conduct a measurement and return the X,Y,Z values

        Usage::

            ok, x, y, z = colorCal.measure()

        Where:
            ok is True/False
            x, y, z are the CIE coordinates

        """
        val = self.sendMessage('MES', timeout=0.5)#use a longish timeout for measurement
        vals=val.split(',')#separate into words
        ok = (vals[0]=='OK00')
        #transform raw x,y,z by calibration matrix
        xyzRaw = numpy.array([vals[1],vals[2],vals[3]], dtype=float)
        x,y,z = numpy.dot(self.calibMatrix, xyzRaw)
        return ok, x, y, z

    def getInfo(self):
        """Queries the device for information

        usage::
            ok, serialNumber, firmwareVersion, firmwareBuild = colorCal.getInfo()

        `ok` will be True/False
        Other values will be a string or None.

        """
        val = self.sendMessage('IDR').split(',')
        ok = (val[0]=='OK00')
        if ok:
            firmware=val[2]
            serialNum=val[4]
            firmBuild=val[-1]
        else:
            firmware=0
            serialNum=0
            firmBuild=0
        return ok, serialNum, firmware, firmBuild

    def calibrateZero(self):
        """This should be done once before any measurements are taken when
        """
        val = self.sendMessage("UZC", timeout=1.0)
        print 'got', val
        if val=='OK00':
            return True
        elif val=='ER11':
            log.error("Could not calibrate ColorCAL2. Is it properly covered?")
        return 0#if we got here there was a problem, either reading or an ER11
    def getCalibMatrix(self):
        """Get the calibration matrix from the device, needed for transforming
        measurements into real-world values.

        This is normally retrieved during __init__ and stored as
            ColorCal.calibMatrix
        so most users don't need to call this function
        """
        matrix=numpy.zeros((3,3),dtype=float)
        #alternatively use 'r99' which gets all rows at once, but then more parsing?
        for rowN in range(3):
            rowName='r0%i' %(rowN+1)
            val = self.sendMessage(rowName, timeout=1.0)
            vals=val.split(',')#convert to list of values
            if vals[0]=='OK00' and len(vals)>1:
                #convert to numpy array
                rawVals=numpy.array(vals[1:], dtype=int)
                floats = _minolta2float(rawVals)
                matrix[rowN,:]=floats
            else:
                print 'ColorCAL got this from command %s: %s' %(rowName, repr(val))
        return matrix
    def _error(self, msg):
        self.OK=False
        log.error(msg)

    def readline(self, size=None, eol='\n\r'):
        """This should be used in place of the standard serial.Serial.readline()
        because that doesn't allow us to set the eol character"""
        #The code here is adapted from
        #    pyserial 2.5: serialutil.FileLike.readline
        #which is released under the python license.
        #Copyright (C) 2001-2010 Chris Liechti
        leneol = len(eol)
        line = bytearray()
        while True:
            c = self.com.read(1)#NB timeout is applied here, so to each char read
            if c:
                line += c
                if line[-leneol:] == eol:
                    break
                if size is not None and len(line) >= size:
                    break
            else:
                break
        return bytes(line)

def _minolta2float(inVal):
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