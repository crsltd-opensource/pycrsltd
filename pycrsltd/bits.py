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

#Acknowledgements:
#    This code written by Jon Peirce <jon@peirce.org.uk>. The BitsPlusPlus code was
#    originally as part of the PsychoPy library (http://www.psychopy.org).

"""Interface to the bits++ (http://www.crsltd.com/) for hi-res luminance/contrast control
"""

DEBUG=True

import numpy
import shaders
from copy import copy
import logging
from OpenGL import GL
try:
    from psychopy.ext import _bits
    haveBitsDLL=True
except:
    haveBitsDLL=False

if DEBUG: #we don't want error skipping in debug mode!
    import shaders
    haveShaders=True
else:
    try:
        import shaders
        haveShaders=True
    except:
        haveShaders=False

bits8BITPALETTEMODE=  0x00000001  #/* normal vsg mode */
NOGAMMACORRECT     =  0x00004000  #/* Gamma correction mode */
GAMMACORRECT       =  0x00008000  #/* Gamma correction mode */
VIDEOENCODEDCOMMS  =  0x00080000 # needs to be set so that LUT is read from screen


class BitsBox:
    """The main class to control a bits++ box.

    If you're using PsychoPy you can usually access Bits++ functions directly
    from your PsychoPy Window
    e.g.::

        from psychopy import visual
        win = visual.Window([800,600], mode='bits++')
        win.bits.setContrast(0.5)#use bits++ to reduce the whole screen contrast by 50%

    """
    def __init__(self,
                    win,
                    contrast=1.0,
                    gamma=[1.0,1.0,1.0],
                    nEntries=256,
                    mode='bits++',):
        self.win = win
        self.contrast=contrast
        self.nEntries=nEntries
        #set standardised name for mode
        if mode in ['bits','bits++']:
            self.mode = 'bits++'
        elif mode in ['color','color++','colour','colour++']:
            self.mode = 'color++'
        elif mode in ['mono','mono++']:
            self.mode = 'mono++'
        else:
            logging.error("Unknown mode '%s' for BitsBox" %mode)

        if len(gamma)>2: # [Lum,R,G,B] or [R,G,B]
            self.gamma=gamma[-3:]
        else:
            self.gamma = [gamma, gamma, gamma]

        if init():
            setVideoMode(NOGAMMACORRECT|VIDEOENCODEDCOMMS)
            self.initialised=True
            logging.debug('found and initialised bits++')
        else:
            self.initialised=False
            logging.warning("couldn't initialise bits++")

        if self.mode == 'bits++':
            #do the processing
            self._HEADandLUT = numpy.zeros((524,1,3),numpy.uint8)
            self._HEADandLUT[:12,:,0] = numpy.asarray([ 36, 63, 8, 211, 3, 112, 56, 34,0,0,0,0]).reshape([12,1])#R
            self._HEADandLUT[:12,:,1] = numpy.asarray([ 106, 136, 19, 25, 115, 68, 41, 159,0,0,0,0]).reshape([12,1])#G
            self._HEADandLUT[:12,:,2] = numpy.asarray([ 133, 163, 138, 46, 164, 9, 49, 208,0,0,0,0]).reshape([12,1])#B
            self.LUT=numpy.zeros((256,3),'d')#just a place holder
            self.setLUT()#this will set self.LUT and update self._LUTandHEAD
        elif haveShaders:
            self.monoModeShader = shaders.compileProgram(fragment=shaders.bitsMonoModeFrag,
                                   attachments=[shaders.gammaCorrectionFrag])
            self.colorModeShader =shaders.compileProgram(fragment=shaders.bitsColorModeFrag,
                                   attachments=[shaders.gammaCorrectionFrag])
            GL.glUseProgram(self.colorModeShader)
            prog = self.colorModeShader
            GL.glUniform1f(GL.glGetUniformLocation(prog, 'sampleSpacing'), 1.0)
            #Set default encoding gamma for power-law shader to (1.0, 1.0, 1.0):
            GL.glUniform3f(GL.glGetUniformLocation(prog, 'ICMEncodingGamma'), 1.0, 1.0, 1.0)
            # Default min and max luminance is 0.0 to 1.0, therefore reciprocal 1/range is also 1.0:
            GL.glUniform3f(GL.glGetUniformLocation(prog, 'ICMMinInLuminance'), 0.0, 0.0, 0.0)
            GL.glUniform3f(GL.glGetUniformLocation(prog, 'ICMMaxInLuminance'), 1.0, 1.0, 1.0)
            GL.glUniform3f(GL.glGetUniformLocation(prog, 'ICMReciprocalLuminanceRange'), 1.0, 1.0, 1.0)
            # Default gain to postmultiply is 1.0:
            GL.glUniform3f(GL.glGetUniformLocation(prog, 'ICMOutputGain'), 1.0, 1.0, 1.0)
            # Default bias to is 0.0:
            GL.glUniform3f(GL.glGetUniformLocation(prog, 'ICMOutputBias'), 0.0, 0.0, 0.0)
            GL.glUniform2f(GL.glGetUniformLocation(prog, 'ICMClampToColorRange'), 0.0, 1.0)
            GL.glUseProgram(0)

    def setLUT(self,newLUT=None, gammaCorrect=True, LUTrange=1.0):
        """Sets the LUT to a specific range of values.

        Note that, if you leave gammaCorrect=True then any LUT values you supply
        will automatically be gamma corrected.

        If BitsBox setMethod is 'fast' then the LUT will take effect on the next
        ``Window.update()`` If the setMethod is 'slow' then the update will take
        place over the next 1-4secs down the USB port.

        **Examples:**
            ``bitsBox.setLUT()``
                builds a LUT using bitsBox.contrast and bitsBox.gamma

            ``bitsBox.setLUT(newLUT=some256x1array)``
                (NB array should be float 0.0:1.0)
                Builds a luminance LUT using newLUT for each gun
                (actually array can be 256x1 or 1x256)

            ``bitsBox.setLUT(newLUT=some256x3array)``
               (NB array should be float 0.0:1.0)
               Allows you to use a different LUT on each gun

        (NB by using BitsBox.setContr() and BitsBox.setGamma() users may not
        need this function!?)
        """

        #choose endpoints
        LUTrange=numpy.asarray(LUTrange)
        if LUTrange.size==1:
            startII = int(round((0.5-LUTrange/2.0)*255.0))
            endII = int(round((0.5+LUTrange/2.0)*255.0))+1 #+1 because python ranges exclude last value
        elif LUTrange.size==2:
            multiplier=1.0
            if LUTrange[1]<=1: multiplier=255.0
            startII= int(round(LUTrange[0]*multiplier))
            endII = int(round(LUTrange[1]*multiplier))+1 #+1 because python ranges exclude last value
        stepLength = 2.0/(endII-startII-1)

        if newLUT is None:
            #create a LUT from scratch (based on contrast and gamma)
            #rampStep = 2.0/(self.nEntries-1)
            ramp = numpy.arange(-1.0,1.0+stepLength, stepLength)
            ramp = (ramp*self.contrast+1.0)/2.0
            #self.LUT will be stored as 0.0:1.0 (gamma-corrected)
            self.LUT[startII:endII,0] = copy(ramp)
            self.LUT[startII:endII,1] = copy(ramp)
            self.LUT[startII:endII,2] = copy(ramp)
        elif type(newLUT) in [float, int] or (newLUT.shape==()):
            self.LUT[startII:endII,0]= newLUT
            self.LUT[startII:endII,1]= newLUT
            self.LUT[startII:endII,2]= newLUT
        elif len(newLUT.shape) == 1: #one dimensional LUT
            #replicate LUT to other channels
            #check range is 0:1
            if newLUT>1.0:
                logging.warning('newLUT should be float in range 0.0:1.0')
            self.LUT[startII:endII,0]= copy(newLUT.flat)
            self.LUT[startII:endII,1]= copy(newLUT.flat)
            self.LUT[startII:endII,2]= copy(newLUT.flat)

        elif len(newLUT.shape) == 2: #one dimensional LUT
            #use LUT as is
            #check range is 0:1
            if max(max(newLUT))>1.0:
                raise AttributeError, 'newLUT should be float in range 0.0:1.0'
            self.LUT[startII:endII,:]= newLUT

        else:
            logging.warning('newLUT can be None, nx1 or nx3')

        #do gamma correction if necessary
        if gammaCorrect==True:
            gamma=self.gamma
            if hasattr(self.win.monitor, 'lineariseLums'):
                self.LUT[startII:endII, : ] = self.win.monitor.lineariseLums(self.LUT[startII:endII, : ], overrideGamma=gamma)

        #update the bits++ box with new LUT
        #get bits into correct order, shape and add to header
        ramp16 = (self.LUT*(2**16-1)).astype(numpy.uint16) #go from ubyte to uint16
        ramp16 = numpy.reshape(ramp16,(256,1,3))
        #set most significant bits
        self._HEADandLUT[12::2,:,:] = (ramp16[:,:,:]>>8).astype(numpy.uint8)
        #set least significant bits
        self._HEADandLUT[13::2,:,:] = (ramp16[:,:,:]&255).astype(numpy.uint8)
        self._HEADandLUTstr = self._HEADandLUT.tostring()

    def _drawLUTtoScreen(self):
        """(private) Used to set the LUT on the Bits++.
        Used to draw the LUT to the screen when in 'bits++' mode (not mono++ or colour++).
        Should not be needed by user if attached to a ``psychopy.visual.Window()``
        since this will automatically draw the LUT as part of the screen refresh.
        """
        #push the projection matrix and set to orthorgaphic

        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glPushMatrix()
        GL.glLoadIdentity()
        GL.glOrtho( 0, self.win.size[0],self.win.size[1], 0, 0, 1 )	#this also sets the 0,0 to be top-left
        #but return to modelview for rendering
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()

        #draw the pixels
        GL_multitexture.glActiveTextureARB(GL_multitexture.GL_TEXTURE0_ARB)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL_multitexture.glActiveTextureARB(GL_multitexture.GL_TEXTURE1_ARB)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glRasterPos2i(0,1)
        GL.glDrawPixelsub(GL.GL_RGB, self._HEADandLUT)
        #GL.glDrawPixels(524,1, GL.GL_RGB,GL.GL_UNSIGNED_BYTE, self._HEADandLUTstr)
        #return to 3D mode (go and pop the projection matrix)
        GL.glMatrixMode( GL.GL_PROJECTION )
        GL.glPopMatrix()
        GL.glMatrixMode( GL.GL_MODELVIEW )

    def setContrast(self,contrast,LUTrange=1.0):
        """Optional parameter LUTrange determines which entries of the LUT
        will be set to this contrast

        :Parameters:
            contrast : float in the range 0:1
                The contrast for the range being set
            LUTrange : float or array
                If a float is given then this is the fraction of the LUT to be used.
                If an array of floats is given, these will specify the start/stop points
                as fractions of the LUT. If an array of ints (0-255) is given these
                determine the start stop *indices* of the LUT

        Examples:
            ``setContrast(1.0,0.5)``
                will set the central 50% of the LUT so that a stimulus with
                contr=0.5 will actually be drawn with contrast 1.0

            ``setContrast(1.0,[0.25,0.5])``

            ``setContrast(1.0,[63,127])``
                will set the lower-middle quarter of the LUT
                (which might be useful in LUT animation paradigms)

        """
        self.contrast = contrast
        #setLUT uses contrast automatically
        self.setLUT(newLUT=None, gammaCorrect=True, LUTrange=LUTrange)

    def setGamma(self, newGamma):
        """Set the LUT to have the requested gamma.
        Currently also resets the LUT to be a linear contrast
        ramp spanning its full range. May change this to read
        the current LUT, undo previous gamm and then apply
        new one?"""
        self.gamma=newGamma
        self.setLUT() #easiest way to update
    def loadShader(self):
        """Load the shader for the current Bits mode (mono++ or color++)
        """
        self.lastShaderProg = GL.glGetIntegerv(GL.GL_CURRENT_PROGRAM)
        if self.mode == 'color++':
            GL.glUseProgram(self.colorModeShader)
            print 'using color shader'
        elif self.mode == 'mono++':
            GL.glUseProgram(self.monoModeShader)
            print 'using mono shader'
        else:
            logging.error('Bits.loadShader() called, but Bits is in %s mode' %self.mode)
    def revertShader(self):
        """Reverts OpenGL to use the shader being used at the point that
        Bits.loadShader() was last called.
        """
        GL.glUseProgram(self.lastShaderProg)


#The following all require access to the dll and aren't likely to have any effect
try:
    import _bits
    haveBitsDLL=True
except:
    haveBitsDLL=False
def init():
    """initialise the bits++ box
    Note that, by default, bits++ will perform gamma correction
    that you don't want (unless you have the CRS calibration device)
    (Recommended that you use the BitsBox class rather than
    calling this directly)
    """
    if haveBitsDLL:
        try:
            retVal = _bits.bitsInit() #returns null if fails?
        except:
            log.error('bits.init() barfed!')
            return 0
    return 1

def setVideoMode(videoMode):
    """set the video mode of the bits++ (win32 only)

    bits8BITPALETTEMODE=  0x00000001  #normal vsg mode

    NOGAMMACORRECT  =  0x00004000  #No gamma correction mode

    GAMMACORRECT    =  0x00008000  #Gamma correction mode

    VIDEOENCODEDCOMMS =  0x00080000

    (Recommended that you use the BitsLUT class rather than
    calling this directly)
    """
    if haveBitsDLL:
        return _bits.bitsSetVideoMode(videoMode)
    else:
        return 1

def reset(noGamma=True):
    """reset the bits++ box via the USB cable by initialising again
    Allows the option to turn off gamma correction
    """
    OK = init()
    if noGamma and OK: setVideoMode(NOGAMMACORRECT)
