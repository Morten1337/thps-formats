import os
import pytest
from pathlib import Path as Path
from thps_formats.utils.reader import BinaryReader


def test_binary_reader():
	with open(Path(__file__).parent.resolve() / 'data' / 'test.dat', 'rb') as inp:
		br = BinaryReader(inp)
		br.seek(0, os.SEEK_SET)
		assert br.read_uint8() == 255
		assert br.read_int8() == -1
		assert br.read_byte() == 0
		assert br.read_byte() == 1

		# seeking past the buffer should fail
		#br.seek(4, os.SEEK_SET)
		#with pytest.raises(Exception):
		#	br.seek(4, os.SEEK_CUR)

		# reading past the buffer should fail
		br.seek(4, os.SEEK_SET)
		with pytest.raises(Exception):
			_ = br.read_uint32()


def test_bytes_reader():
	with open(Path(__file__).parent.resolve() / 'data' / 'test.dat', 'rb') as inp:
		br = BinaryReader(BinaryReader(inp).read_bytes(4))
		br.seek(0, os.SEEK_SET)
		assert br.read_uint8() == 255
		assert br.read_int8() == -1
		assert br.read_byte() == 0
		assert br.read_byte() == 1

		# seeking past the buffer should fail
		#br.seek(4, os.SEEK_SET)
		#with pytest.raises(Exception):
		#	br.seek(4, os.SEEK_CUR)

		# reading past the buffer should fail
		br.seek(4, os.SEEK_SET)
		with pytest.raises(Exception):
			_ = br.read_uint32()
