import io
from pathlib import Path as Path

from thps_formats.utils.writer import BinaryWriter

import xmltodict
from PIL import Image
import png

import copy


# -------------------------------------------------------------------------------------------------
def filter_chars_by_id_range(chars, min_id, max_id, exclude_id=None):
	"""
	Filter characters by their ID range, considering ASCII and extended ASCII codes.

	Args:
	- chars: List of characters (dictionaries) to filter.
	- min_id: Minimum ASCII or extended ASCII code (inclusive).
	- max_id: Maximum ASCII or extended ASCII code (inclusive).
	- exclude_id: An ASCII code to exclude from the results.

	Returns:
	- A list of characters within the specified ASCII or extended ASCII code range.
	"""
	if exclude_id is not None:
		return [c for c in chars if min_id <= int(c['@id']) <= max_id and int(c['@id']) != exclude_id]
	else:
		return [c for c in chars if min_id <= int(c['@id']) <= max_id]


# -------------------------------------------------------------------------------------------------
def remap_chars_to_lower_if_needed(chars, condition, char_range):
	"""
	Converts uppercase characters to lowercase if a condition is met by adding 32 to their codes.

	Args:
	- chars: The list of characters (dictionaries) to possibly modify.
	- condition: A boolean condition that, if True, triggers the conversion.
	- char_range: The character range (as returned by filter_chars_by_id_range) to convert.

	Modifies chars in place if the condition is True, based on ASCII conversion logic.
	"""
	if condition:
		for c in char_range:
			m = copy.deepcopy(c)
			m['@id'] = str(int(m['@id']) + 32) # Convert to lowercase by adding 32 to the ASCII code
			chars.append(m)


# -------------------------------------------------------------------------------------------------
class FontBitmap:

	def __init__(self):
		self.width = 0
		self.height = 0
		self.bpp = 8
		self.unknown1 = 72 # @thug2 unknown
		self.unknown2 = 69 # @thug2 unknown
		self.unknown3 = 28680 # @thug2 unknown
		self.data = None
		self.palette = None

	# ---------------------------------------------------------------------------------------------
	@classmethod
	def from_png(cls, filepath):

		buffer = io.BytesIO()
		Image.open(filepath).convert('RGBA').quantize(method=2).save(buffer, format='PNG')
		buffer.seek(0)

		reader = png.Reader(file=buffer)
		width, height, pixels, metadata = reader.read()

		if not metadata.get('palette'):
			raise ValueError('Palette data is missing for the given bitmap!')

		bitmap = cls()
		bitmap.data = bytes([p for row in pixels for p in row])
		bitmap.palette = bytes([p for sublist in metadata['palette'] for p in sublist])
		bitmap.width = width
		bitmap.height = height

		return bitmap

	# ---------------------------------------------------------------------------------------------
	def dump(self, writer):
		writer.write_uint16(self.width)
		writer.write_uint16(self.height)
		writer.write_uint16(self.bpp)
		writer.write_int16(self.unknown1)
		writer.write_int16(self.unknown2)
		writer.write_int16(self.unknown3)
		writer.write_bytes(self.data)
		writer.write_bytes(self.palette)
		return True 


# -------------------------------------------------------------------------------------------------
class Font:
	
	# ---------------------------------------------------------------------------------------------
	def __init__(self, params={}):
		self.baseline_height = 0
		self.default_height = 0
		self.bitmap = None
		self.characters = []
		self.dimensions = []

	# ---------------------------------------------------------------------------------------------
	@classmethod
	def from_xml(cls, filepath, params={}):
		filepath = Path(filepath).resolve()
		font = cls(params)

		if not filepath.exists():
			raise FileNotFoundError(f'File does not exist... {filepath}')

		try:
			font.convert(filepath)
		except Exception as exeption:
			raise exeption

		return font

	# ---------------------------------------------------------------------------------------------
	def to_file(self, filepath, params):
		filepath = Path(filepath).resolve()
		with open(filepath, 'wb') as file:
			return self.dump(BinaryWriter(file))
		return False

	# ---------------------------------------------------------------------------------------------
	def dump(self, writer):
		size = 4
		size += 2 + 2 + 2 + 2 + 2 + 2
		size += len(self.bitmap.data)
		size += len(self.bitmap.palette)
		writer.write_uint32(size)
		writer.write_uint32(1) # @thug2 unknown
		writer.write_uint32(len(self.characters))
		writer.write_uint32(self.default_height)
		writer.write_uint32(self.baseline_height)

		for c in self.characters:
			writer.write_uint16(self.baseline_height)
			writer.write_bytes(bytearray(c, encoding='utf-16')[2:4]) # ehh
			writer.write_uint16(0) # @thug2 unknown

		remainder = (4 + size + (len(self.dimensions) * 8))
		writer.write_uint32(remainder)
		self.bitmap.dump(writer)

		writer.write_uint32(len(self.dimensions))
		for d in self.dimensions:
			all(writer.write_uint16(unit) for unit in d)

		return True

	# ---------------------------------------------------------------------------------------------
	def convert(self, xmlpath):

		# load bmfnt xml file
		xmlpath = Path(xmlpath).resolve()
		with open(xmlpath, 'rb') as file:
			xml = xmltodict.parse(file.read())

		# parse fnt data
		_common = xml['font']['common']
		_chars = xml['font']['chars']['char']
		self.default_height = int(_chars[0]['@height'])
		self.baseline_height = int(_common['@base'])

		# filter characters by ascii ranges for uppercase and their extended counterparts
		uppercase_latin = filter_chars_by_id_range(_chars, 65, 90) # 'A' to 'Z'
		uppercase_latin_ext = filter_chars_by_id_range(_chars, 192, 223) # 'À' to 'ß' with exceptions

		lowercase_latin = filter_chars_by_id_range(_chars, 97, 122) # 'a' to 'z'
		lowercase_latin_ext = filter_chars_by_id_range(_chars, 224, 1000, exclude_id=255) # 'à' to 'ÿ' excluding 'ÿ'

		# check if conversion conditions are met based on character presence
		should_remap_1 = not lowercase_latin and len(uppercase_latin) == 26
		should_remap_2 = not lowercase_latin_ext and len(uppercase_latin_ext) == 30

		# perform conversion if conditions are met
		remap_chars_to_lower_if_needed(_chars, should_remap_1, uppercase_latin)
		remap_chars_to_lower_if_needed(_chars, should_remap_2, uppercase_latin_ext)

		# handle characters
		for c in _chars:
			# yoffset, character, thug2 unknown
			self.characters.append(str(chr(int(c['@id']))))

		# handle dimensions
		for c in _chars:
			self.dimensions.append(tuple(int(c[key]) for key in ['@x', '@y', '@width', '@height']))

		# ensure that the font only has one texture atlas...
		# you'll have to tweak the bmfont scaling and characters to fit
		if int(xml['font']['common']['@pages']) != 1:
			raise NotImplementedError('We only support single bitmap fonts currently!')

		# handle bitmap
		atlaspath = xmlpath.with_name(xml['font']['pages']['page']['@file'])
		self.bitmap = FontBitmap.from_png(atlaspath)
