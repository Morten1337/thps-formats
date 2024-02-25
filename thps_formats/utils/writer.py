import io
import struct
import binascii


class BinaryWriter(object):

	def __init__(self, stream):
		if isinstance(stream, bytes):
			self.stream = io.BytesIO(stream)
		else:
			self.stream = stream

	def write_byte(self, value):
		if type(value) is bytes:
			self.stream.write(value)
		elif type(value) is str:
			self.stream.write(value.encode)
		elif type(value) is int:
			self.stream.write(bytes([value]))

	def write_bytes(self, value, unhex=True):
		if unhex:
			try:
				value = binascii.unhexlify(value)
			except binascii.Error:
				pass
		return self.stream.write(value)

	def pack(self, fmt, data):
		return self.write_bytes(struct.pack(fmt, data), unhex=False)

	def write_char(self, value):
		return self.pack('c', value)

	def write_float(self, value, endian='<'):
		return self.pack(f'{endian}f', value)

	def write_double(self, value, endian='<'):
		return self.pack(f'{endian}d', value)

	def write_int8(self, value, endian='<'):
		return self.pack(f'{endian}b', value)

	def write_uint8(self, value, endian='<'):
		return self.pack(f'{endian}B', value)

	def write_bool(self, value):
		return self.pack('?', value)

	def write_int16(self, value, endian='<'):
		return self.pack(f'{endian}h', value)

	def write_uint16(self, value, endian='<'):
		return self.pack(f'{endian}H', value)

	def write_int32(self, value, endian='<'):
		return self.pack(f'{endian}i', value)

	def write_uint32(self, value, endian='<'):
		return self.pack(f'{endian}I', value)

	def write_int64(self, value, endian='<'):
		return self.pack(f'{endian}q', value)

	def write_uint64(self, value, endian='<'):
		return self.pack(f'{endian}Q', value)

	def write_string(self, value, encoding='utf-8'):
		if type(value) is str:
			value = value.encode(encoding)
		self.write_bytes(binascii.hexlify(bytearray(value)).decode(encoding))

	def write_character(self, value, encoding='utf-8'):
		if type(value) is str:
			value = value.encode(encoding)
		self.write_bytes(binascii.hexlify(bytearray(value)).decode(encoding))
