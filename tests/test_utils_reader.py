from pathlib import Path as Path
from thps_formats.utils.reader import BinaryReader


def test_binary_reader():
	with open(Path(__file__).parent.resolve() / 'data' / 'test.dat', 'rb') as inp:
		br = BinaryReader(inp)
		assert br.read_uint8() == 255
		assert br.read_int8() == -1
		assert br.read_byte() == 0
		assert br.read_byte() == 1
