import os
import io
import struct


class BinaryReader(object):

	def __init__(self, stream):
		if isinstance(stream, bytes):
			self.stream = io.BytesIO(stream)
		else:
			self.stream = stream

	def seek(self, offset, whence=os.SEEK_SET):
		return self.stream.seek(offset, whence)

	def unpack(self, fmt, length=1):
		return struct.unpack(fmt, self.stream.read(length))[0]

	def read_byte(self, do_ord=True):
		if do_ord:
			return ord(self.stream.read(1))
		return self.stream.read(1)

	def read_bytes(self, length):
		value = self.stream.read(length)
		return value

	def read_bool(self):
		return self.unpack('?')

	def read_char(self):
		return self.unpack('c')

	def read_character(self, size=1, encoding='utf-8'):
		return self.read_bytes(size).decode(encoding)

	def read_float(self, endian='<'):
		return self.unpack(f'{endian}f', 4)

	def read_double(self, endian='<'):
		return self.unpack(f'{endian}d', 8)

	def read_int8(self, endian='<'):
		return self.unpack(f'{endian}b')

	def read_uint8(self, endian='<'):
		return self.unpack(f'{endian}B')

	def read_int16(self, endian='<'):
		return self.unpack(f'{endian}h', 2)

	def read_uint16(self, endian='<'):
		return self.unpack(f'{endian}H', 2)

	def read_int32(self, endian='<'):
		return self.unpack(f'{endian}i', 4)

	def read_uint32(self, endian='<'):
		return self.unpack(f'{endian}I', 4)

	def read_int64(self, endian='<'):
		return self.unpack(f'{endian}q', 8)

	def read_uint64(self, endian='<'):
		return self.unpack(f'{endian}Q', 8)
