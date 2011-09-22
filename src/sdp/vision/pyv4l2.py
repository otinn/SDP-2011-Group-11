#!/usr/bin/env python

# Released under the GPL v3 by Jackson Yee (jackson@gotpossum.com)
# Copyright 2008
#
# Project site: http://code.google.com/p/python-video4linux2/

from ctypes import *
import os
import Image as PILImage

lib = cdll.LoadLibrary("./libpyv4l2.so")
lib.Error.restype = c_char_p
lib.MMap.restype = c_void_p

# *********************************************************************
def ListFlags(value, flags):
	return [k for k, v in flags.iteritems() if value & v]

# *********************************************************************
def FindKey(d, value):
	for k, v in d.iteritems():
		if v == value:
			return k
			
	return None
		
# *********************************************************************
class Capabilities(Structure):
	_fields_	=	[
		('driver',				c_char * 16),
		('card',					c_char * 32),
		('businfo',				c_char * 32),
		('version',				c_uint32),
		('capabilities',	c_uint32),
		('reserved',			c_uint32 * 4),
	]

# *********************************************************************
class Input(Structure):
	_fields_	=	[
		('index',					c_uint),
		('name',					c_char * 32),
		('type',					c_uint),
		('audioset',			c_uint),
		('tuner',					c_uint),
		('std',						c_ulonglong),
		('status',				c_uint),
		('reserved',			c_uint * 4),
	]
	
# *********************************************************************
class PixFormat(Structure):
	_fields_	=	[
		('type',					c_long),
		('width',					c_uint32),
		('height',				c_uint32),
		('pixelformat',		c_char * 4),
		('field',					c_uint32),
		('bytesperline',	c_uint32),
		('sizeimage',			c_uint32),
		('colorspace',		c_uint32),
		('priv',					c_uint32),
		('fps_num',                 c_uint32),
		('fps_den',                 c_uint32),
		('blank_space',             c_char * 512),

	]
	
# *********************************************************************
class RequestBuffers(Structure):
	_fields_	=	[
		('count',					c_uint32),
		('type',					c_uint32),
		('memory',				c_uint32),
		('reserved',			c_uint32 * 2),
	]
	
# *********************************************************************
class TimeCode(Structure):
	_fields_	=	[
		('type',					c_uint32),
		('flags',					c_uint32),
		('frames',				c_ubyte),
		('seconds',				c_ubyte),
		('minutes',				c_ubyte),
		('hours',					c_ubyte),
		('userbits',			c_ubyte * 4),
	]

# *********************************************************************
class Buffer(Structure):
	class M(Union):
		_fields_	=	[
			('offset',				c_uint32),
			('userptr',				c_ulong),
		]
		
	_fields_	=	[
		('index',					c_uint32),
		('type',					c_uint32),
		('bytesused',			c_uint32),
		('flags',					c_uint32),
		('field',					c_uint32),
		('seconds',				c_long),
		('nanoseconds',		c_long),
		('timecode',			TimeCode),
		('sequence',			c_uint32),
		('memory',				c_uint32),
		('m',							M),
		('length',				c_uint32),
		('input',					c_uint32),
		('reserved',			c_uint32),
	]
	
# *********************************************************************
class Format(Structure):
	_fields_	=	[
		('index',					c_uint32),
		('type',					c_uint32),
		('flags',					c_uint32),
		('description',		c_char * 32),
		('pixelformat',		c_char * 4),
		('reserved',			c_uint32 * 4),
	]
	
# *********************************************************************
class Device(object):
	
	fd						=	0
	device				=	None
	driver				=	None
	card					=	None
	businfo				=	None
	numinputs			=	None
	buffer				=	None
	format				=	None
	caps					=	[]
	buffers				=	[]
	
	capabilities	=	{
		'Capture'							:	0x01,
		'Output'							:	0x02,
		'Overlay'							:	0x04,
		'VBICapture'					:	0x10,
		'VBIOutput'						:	0x20,
		'SlicedVBICapture'		:	0x40,
		'SlicedVBIOutput'			:	0x80,
		'RDSCapture'					:	0x100,
		'VideoOutputOverlay'	:	0x200,
		'Tuner'								:	0x10000,
		'Audio'								:	0x20000,
		'Radio'								:	0x40000,
		'ReadWrite'						:	0x1000000,
		'AsyncIO'							:	0x2000000,
		'Streaming'						:	0x4000000,
	}
	
	standards	=	{
		'PAL_B'								:	0x01,
		'PAL_B1'							:	0x02,
		'PAL_G'								:	0x04,
		'PAL_H'								:	0x08,
		'PAL_I'								:	0x10,
		'PAL_D'								:	0x20,
		'PAL_D1'							:	0x40,
		'PAL_K'								:	0x80,
		'PAL_M'								:	0x100,
		'PAL_N'								:	0x200,
		'PAL_Nc'							:	0x400,
		'PAL_60'							:	0x800,
		'NTSC_M'							:	0x1000,
		'NTSC_M_JP'						:	0x2000,
		'NTSC_443'						:	0x4000,
		'NTSC_M_KR'						:	0x8000,
		'SECAM_B'							:	0x10000,
		'SECAM_D'							:	0x20000,
		'SECAM_G'							:	0x40000,
		'SECAM_H'							:	0x80000,
		'SECAM_K'							:	0x100000,
		'SECAM_K1'						:	0x200000,
		'SECAM_L'							:	0x400000,
		'SECAM_LC'						:	0x800000,
		'ATSC_8_VSB'					:	0x1000000,
		'ATSC_16_VSB'					:	0x2000000,
		'PAL'									:	0xff,
		'NTSC'								:	0xb000,
	}
	
	statuses	=	{
		'NoPower'							:	0x01,
		'NoSignal'						:	0x02,
		'NoColor'							:	0x04,
		'NoHLock'							:	0x100,
		'ColorKill'						:	0x200,
		'NoSync'							:	0x10000,
		'NoEQU'								:	0x20000,
		'NoCarrier'						:	0x40000,
		'Macrovision'					:	0x1000000,
		'NoAccess'						:	0x2000000,
		'NoVTR'								:	0x4000000,
	}
	
	buftypes	=	{
		'Capture'							:	0x01,
		'Output'							:	0x02,
		'Overlay'							:	0x03,
		'VBICapture'					:	0x04,
		'VBIOutput'						:	0x05,
		'SlicedVBICapture'		:	0x06,
		'SlicedVBIOutput'			:	0x07,
		'VideoOutputOverlay'	:	0x08,
		'Private'							:	0x80,
	}
	
	fields	=	{
		'Any'							:	0x00,
		'None'						:	0x01,
		'Top'							:	0x02,
		'Bottom'					:	0x03,
		'Interlaced'			:	0x04,
		'SeqTB'						:	0x05,
		'SeqBT'						:	0x06,
		'Alternate'				:	0x07,
		'InterlacedTB'		:	0x08,
		'InterlacedBT'		:	0x09,
	}
	
	pixelformats = (
		'RGB1',
		'R444',
		'RGBO',
		'RGBP',
		'RGBQ',
		'RGBR',
		'BGR3',
		'RGB3',
		'BGR4',
		'RGB4',
		'BA81',
		'BA82',
		'Y444',
		'YUVO',
		'YUVP',
		'YUV4',
		'GREY',
		'Y16 ',
		'YUYV',
		'UYVY',
		'Y41P',
		'YV12',
		'YU12',
		'YVU9',
		'YUV9',
		'422P',
		'411P',
		'NV12',
		'NV21',
		'JPEG',
		'MPEG',
		'DVSD',
		'E625',
		'HI24',
		'HM12',
		'MJPG',
		'PWC1',
		'PWC2',
		'S910',
		'WNVA',
		'YYUV',
	)
	
	yuvformats = (
		'Y444',
		'YUVO',
		'YUVP',
		'YUV4',
		'GREY',
		'Y16 ',
		'YUYV',
		'UYVY',
		'Y41P',
		'YV12',
		'YU12',
		'YVU9',
		'YUV9',
		'422P',
		'411P',
	)
	
	resolutions = (
		
		# NTSC/PAL resolutions
		(320,	240),
		(320,	480),
		(320,	576),
		(352,	240),
		(384,	288),
		(384,	576),
		(480,	480),
		(480,	576),
		(512,	480),
		(512,	576),
		(640,	480),
		(640,	576),
		(720,	480),
		(768,	576),
		
		# 4:3 VGA resolutions
		(800,	600),
		(1024,	768),
		(1280,	960),
		(1280,	1024),
		(1400,	1050),
		(1600,	1200),
		(2048,	1536),

		# Other VGA resolutions
		(800,	480),
		(854,	480),
		(1024,	600),
		(1152,	768),
		(1280,	720),
		(1280,	768),
		(1366,	768),
		(1280,	800),
		(1440,	900),
		(1440,	960),
		(1680,	1050),
		(1920,	1080),
		(2048,	1080),
		(1920,	1200),
	)
	
	# -------------------------------------------------------------------
	def __init__(self, dev):
		if dev:
			self.Open(dev)
	
	# -------------------------------------------------------------------
	@classmethod
	def List(self):
		"""Returns the full path of all available video devices."""
		files = os.listdir('/dev')
		ls = []		
		
		for f in files:
			if 'video' in f:
				if f != 'video':
					ls.append( '/dev/' + f)
		
		return ls
		
	# -------------------------------------------------------------------
	def Open(self, dev):
		if self.fd:
			self.Close(fd)
		
		self.fd = lib.Open(dev)
		
		if self.fd == -1:
			self.fd = 0
			raise Exception('Could not open video device %s:\t%i: %s' % 
				(dev, lib.Errno(), lib.Error())
			)
		
		self.device	=	dev
		
	# -------------------------------------------------------------------
	def Close(self):
		if self.fd:
			lib.Close(fd)
		
	# -------------------------------------------------------------------
	def QueryCaps(self):
		"""Queries the driver for what this card is capable of.
		
		After this function completes, the driver, card, businfo,
		and caps properties will be filled."""
		s = Capabilities()
		
		if lib.QueryCaps(self.fd, byref(s)) == -1:
			raise Exception('Could not query capabilities:\t%i: %s' % 
				(lib.Errno(), lib.Error())
			)		
		
		self.driver		= s.driver
		self.card			=	s.card
		self.businfo	=	s.businfo
		self.caps			=	ListFlags(s.capabilities, self.capabilities)		
		
	# -------------------------------------------------------------------
	def EnumInput(self, input):
		"""Returns information concerning the given input in a list
		containing [name, type, audioset, tuner, standard, status]
		"""
		s = Input()
		s.index = input
		
		if lib.EnumInput(self.fd, byref(s)) == -1:
			raise Exception('Could not enumerate input %i:\t%i: %s' % 
				(input, lib.Errno(), lib.Error())
			)		
			
		if input > self.numinputs:
			self.numinputs = input
		
		ls = []
		
		ls.append(s.name)
		
		if s.type == 1:
			ls.append('tuner')
		else:
			ls.append('camera')
		
		ls.append(s.audioset)
		ls.append(s.tuner)
		ls.append( ListFlags(s.std, self.standards) )
		ls.append( ListFlags(s.status, self.statuses) )
		
		return ls
			
	# -------------------------------------------------------------------
	def EnumFormats(self, type):
		"""Returns information about the available formats for 
		the current input.
		
		The formats are returned in a list of tuples containing
		(fourcc, description)
		
		type can be any of the following defined in Device.buftypes:
			Capture
			Output
			Overlay
			Private
		"""
		s = Format()
		i = 0
		ls = []
		
		s.type = type
		
		while True:
			s.index = i
			if lib.EnumFormat(self.fd, byref(s)) == -1:
				break
			ls.append( (s.pixelformat, s.description) )
			i += 1
		
		return ls
			
	# -------------------------------------------------------------------
	def SetInput(self, input):
		"""Sets the device to the given input.
		"""
		if lib.SetInput(self.fd, input) == -1:
			raise Exception('Could not set input %i:\t%i: %s' % 
				(input, lib.Errno(), lib.Error())
			)		
			
	# -------------------------------------------------------------------
	def SetStandard(self, standard):
		"""Sets the device to the given standard.
		"""
		if lib.SetStandard(self.fd, standard) == -1:
			raise Exception('Could not set standard %i:\t%i: %s' % 
				(FindKey(self.standards, standard), 
					lib.Errno(), 
					lib.Error()
				)
			)		
			
	# -------------------------------------------------------------------
	def SetField(self, field):
		"""Sets the device to the given standard.
		"""
		self.GetFormat()
		self.format.field = field
		self.SetFormat()
			
	# -------------------------------------------------------------------
	def GetFormat(self):
		"""Sets the device to the given standard.
		"""
		if not self.format:
			self.format = PixFormat()
			self.format.type = self.buftypes['Capture']
		
		if lib.GetFormat(self.fd, byref(self.format)) == -1:
			raise Exception('Could not get format:\t%i: %s' % 
				(lib.Errno(), 
					lib.Error()
				)
			)		
		
	# -------------------------------------------------------------------
	def SetFormat(self):
		"""Sets the device to the given standard.
		"""
		if lib.SetFormat(self.fd, byref(self.format)) == -1:
			raise Exception('Could not set format:\t%i: %s' % 
				(lib.Errno(), 
					lib.Error()
				)
			)		
			
	# -------------------------------------------------------------------
	def GetPixelFormats(self):
		"""Sets the device to the given standard.
		"""
		
		self.GetFormat()
		
		ls = []
		
		for v in self.pixelformats:
			try:
				self.format.pixelformat = v
				self.SetFormat()
				ls.append(v)
			except Exception, e:
				pass
		
		return ls
		
	# -------------------------------------------------------------------
	def SetPixelFormat(self, format):
		self.GetFormat()
		self.format.pixelformat = format
		self.SetFormat()
		
	# -------------------------------------------------------------------
	def GetResolutions(self):
		"""Sets the device to the given standard.
		"""
		
		self.GetFormat()
		ls = []
		f = self.format
		
		for v in self.resolutions:
			try:
				f.width, f.height = v
				
				self.SetFormat()
				
				if f.width == v[0] and f.height == v[1]:
					ls.append( (f.width, f.height) )
			except Exception, e:
				pass
		
		return ls
		
	# -------------------------------------------------------------------
	def SetResolution(self, w, h):
		"""Sets the device to the given standard.
		"""
		
		self.GetFormat()
		self.format.width = w
		self.format.height = h		
		self.SetFormat()
		
	# -------------------------------------------------------------------
	def __del__(self):
		self.UnmapBuffers()
		if lib:
			lib.Close(self.fd)		
			
	# -------------------------------------------------------------------
	def Read(self):
		if not self.buffer:
			if not self.format:
				self.GetFormat()
			self.buffer = create_string_buffer(self.format.sizeimage)
			
		lib.read(self.fd, self.buffer, self.format.sizeimage)
		
	# -------------------------------------------------------------------
	def RequestBuffers(self, numbuffers, type = 1, memory = 1):
		s = RequestBuffers()
		s.count		=	numbuffers
		s.type		=	type
		s.memory	=	memory
		
		if lib.RequestBuffers(self.fd, byref(s)) == -1:
			raise Exception('Could not request %i buffers:\t%i: %s' % 
				(	numbuffers,
					lib.Errno(), 
					lib.Error()
				)
			)		
			
		return s.count
		
	# -------------------------------------------------------------------
	def MapBuffers(self, count):
		b = Buffer()
		b.type		=	1
		b.memory	=	1
			
		for i in xrange(0, count):
			b.index		=	i
			
			self.QueryBuf(b)
			
			start = lib.MMap(self.fd, b.length, b.m.offset)
			
			if start == -1:
				raise Exception('Could not map buffer %i:\t%i: %s' % 
					(	i,
						lib.Errno(), 
						lib.Error()
					)
				)		
			
			self.buffers.append( (i, start, b.length) )
		
	# -------------------------------------------------------------------
	def UnmapBuffers(self):
		for b in self.buffers:
			lib.MUnmap(b[1], b[2])
		self.buffers = []
		
	# -------------------------------------------------------------------
	def QueryBuf(self, buf):
		if lib.QueryBuf(self.fd, byref(buf)) == -1:
			raise Exception('Could not query buffer:\t%i: %s' % 
				(	lib.Errno(), 
					lib.Error()
				)
			)		
		
	# -------------------------------------------------------------------
	def StreamOn(self, type = 1):
		if lib.StreamOn(self.fd) == -1:
			raise Exception('Could not start streaming:\t%i: %s' % 
				(	lib.Errno(), 
					lib.Error()
				)
			)		
		
	# -------------------------------------------------------------------
	def StreamOff(self, type = 1):
		if lib.StreamOff(self.fd) == -1:
			raise Exception('Could not end streaming:\t%i: %s' % 
				(	lib.Errno(), 
					lib.Error()
				)
			)		
		
	# -------------------------------------------------------------------
	def QueueBuffer(self, buf):
		if lib.Queue(self.fd, byref(buf)) == -1:
			raise Exception('Could not queue buffer:\t%i: %s' % 
				(	lib.Errno(), 
					lib.Error()
				)
			)		
		
	# -------------------------------------------------------------------
	def DequeueBuffer(self, buf):
		if lib.Dequeue(self.fd, byref(buf)) == -1:
			raise Exception('Could not dequeue buffer:\t%i: %s' % 
				(	lib.Errno(), 
					lib.Error()
				)
			)		
		
	# -------------------------------------------------------------------
	def SetupStreaming(self, numbuffers, callback):
		"""Convenience function to setup mmap streaming with 
		the requested number of buffers and a callback function 
		to be called whenever a buffer is filled.
		
		The callback function is setup as
		
		def callback(Device d, Buffer b, ctypes.c_void_p p)
		
		To continue streaming, the callback should return True. Returning
		False will result in streaming being discontinued and all existing
		buffers returned.
		"""
		self.MapBuffers( self.RequestBuffers(numbuffers)	)
		self.StreamOn()
		
		b = Buffer()
		b.type		=	1
		b.memory	=	1
		
		for i in xrange(0, len(self.buffers) ):
			b.index	=	i
			self.QueueBuffer(b)
		
		self.StreamOn()
		
		while True:
			self.DequeueBuffer(b)
			if not callback(self, 
					b, 
					string_at( self.buffers[b.index][1], self.buffers[b.index][2] ) 
				):
				break
			self.QueueBuffer(b)
		
		self.StreamOff()
		
		self.UnmapBuffers()
		
	# -------------------------------------------------------------------
	def SaveJPEG(self, filename, q = 70, buffer = None):
		"""Saves the current buffer to filename as a JPEG image.
		"""
		p = self.format.pixelformat
		
		if p == 'RGB4':
			p = 'RGBA'
		elif p == 'BGR3':
			p = 'BGR'
		elif p == 'RGB3':
			p = 'RGB'
			
		if not buffer:
			buffer	= self.buffer
		
		img = PILImage.frombuffer('RGB', 
			(self.format.width, self.format.height),
			buffer,
			'raw',
			p,
			0,
			1)
		img.save(filename, 'jpeg', quality = q)

# =====================================================================
if __name__ == '__main__':
	ls = Device.List()
	print 'Available devices: ', ls
	
	for i in ls:
		print '\t', i
	
		d = Device(i)
		d.QueryCaps()
		
		print 'Capabilities:\t'
		
		for i in d.caps:
			print '\t', i	
		
		try:
			for i in range(0, 32):
				r = d.EnumInput(i)
				print """Input %i:
	\tName:\t%s
	\tType:\t%s
	\tStandards: %s""" % (i,
					r[0],
					r[1],
					r[4],
					)
		except Exception, e:
			pass
		
		d.SetInput(0)
		d.SetStandard(d.standards['NTSC'])
		
		
		print 'Pixel formats: '

		for i in d.EnumFormats(d.buftypes['Capture']):
			print '\t%s\t%s' % i	
		
		print 'Resolutions: '
		
		for i in d.GetResolutions():
			print '\t%ix%i' % (i[0], i[1])
			
