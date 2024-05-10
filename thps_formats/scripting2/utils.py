import re

from thps_formats.scripting2.crc32 import crc32_generate
from thps_formats.scripting2.enums import TokenType
import thps_formats.scripting2.error as error


# -------------------------------------------------------------------------------------------------
def extract_numbers_to_tuple(value):
	stripped_string = re.sub(r'[^\d,.-]', '', value)
	segments = stripped_string.split(',')
	# Use list comprehension to process segments
	numbers = [float(segment) for segment in segments if re.fullmatch(r'^-?\d*\.\d+$', segment) or re.fullmatch(r'^-?\d+$', segment)]
	# Identify invalid segments
	invalid_numbers = [segment for segment in segments if not (re.fullmatch(r'^-?\d*\.\d+$', segment) or re.fullmatch(r'^-?\d+$', segment)) and segment]
	if invalid_numbers:
		raise error.InvalidFormatError(F"Unable to parse one or more numbers in the vector... {invalid_numbers}")
	return tuple(numbers), len(numbers)


# -------------------------------------------------------------------------------------------------
def tohex(val, nbits):
	return hex((val + (1 << nbits)) % (1 << nbits))


# -------------------------------------------------------------------------------------------------
def strip_hash_string_stuff(value):
	return value[2:-1] # #"hello" -> hello


# -------------------------------------------------------------------------------------------------
def strip_argument_string_stuff(value):
	return value[1:-1] # <hello> -> hello


# -------------------------------------------------------------------------------------------------
def handle_string_stuff(value):
	if value[0] == '"':
		token = TokenType.STRING
	else:
		token = TokenType.LOCALSTRING
	return token, value[1:-1].replace("\\'", "'").replace('\\"', '"').replace('\\\\', '\\')


# -------------------------------------------------------------------------------------------------
def resolve_checksum_name_tuple(value):

	if value[0] is not None:
		return value[0] # return checksum name string ex "hello"

	if value[1] is not None and isinstance(value[1], int):
		# @todo: lookup name from table 
		return F"{value[1]:#010x}" # return formatted checksum string "0xc9ef5979"

	raise ValueError('Trying to resolve checksum name, but no name or checksum was passed...')


# -------------------------------------------------------------------------------------------------
def resolve_checksum_tuple(value):

	# if we have the name string generate the checksum
	if value[0] is not None:
		checksum = crc32_generate(value[0])
		#print(F"Resolving checksum {checksum:#010x}")
		return checksum, value[0]

	# if we (only) have the checksum, just return it
	if value[1] is not None and isinstance(value[1], int):
		checksum = value[1]
		#print(F"Resolving checksum {checksum:#010x}")
		return checksum, None

	raise ValueError('Trying to resolve checksum, but no name or checksum was passed...')


# -------------------------------------------------------------------------------------------------
def is_token_type_random_keyword(token):
	return token in (
		TokenType.KEYWORD_RANDOM,
		TokenType.KEYWORD_RANDOM2,
		TokenType.KEYWORD_RANDOMNOREPEAT,
		TokenType.KEYWORD_RANDOMPERMUTE,
	)


# -------------------------------------------------------------------------------------------------
def is_token_type_primitive(token):
	return token in (
		TokenType.NAME,
		TokenType.INTEGER,
		TokenType.HEXINTEGER,
		TokenType.FLOAT,
		TokenType.PAIR,
		TokenType.VECTOR,
		TokenType.STRING,
		TokenType.LOCALSTRING,
	)
