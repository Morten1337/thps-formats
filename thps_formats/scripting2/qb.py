import os
import io
import re

from colorama import Fore, Back, Style
import colorama

from pathlib import Path as Path

from thps_formats.utils.writer import BinaryWriter
from thps_formats.shared.enums import GameType, GameVersion
from thps_formats.scripting2.enums import TokenType
from thps_formats.scripting2.crc32 import crc32_generate

import thps_formats.scripting2.errors as errors
from thps_formats.scripting2.errors import (print_token_error_message,highlight_error_with_indicator)

# @warn: probably shouldnt have this here...
colorama.init(autoreset=True)

# --- todo ----------------------------------------------------------------------------------------
# - tokenizer->lexer->compiler
# - token post-processing
# 	- Jumps
# - #raw bytes
# - fix incorrect line numbers
# - improve error message handling


# -------------------------------------------------------------------------------------------------
def extract_numbers_to_tuple(value):
	stripped_string = re.sub(r'[^\d,.-]', '', value)
	segments = stripped_string.split(',')
	# Use list comprehension to process segments
	numbers = [float(segment) for segment in segments if re.fullmatch(r'^-?\d*\.\d+$', segment) or re.fullmatch(r'^-?\d+$', segment)]
	# Identify invalid segments
	invalid_numbers = [segment for segment in segments if not (re.fullmatch(r'^-?\d*\.\d+$', segment) or re.fullmatch(r'^-?\d+$', segment)) and segment]
	if invalid_numbers:
		raise errors.InvalidFormatError(f'Unable to parse one or more numbers in the vector... {invalid_numbers}')
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
def skip_random_operator(iterator):
	parenth_count = 0
	# @todo: skip whitespace
	next_token = next(iterator)
	if next_token['type'] is not TokenType.OPENPARENTH:
		raise errors.InvalidFormatError("Random keyword must be followed by an open parenthesis...")

	for token in iterator:
		if token['type'] is TokenType.ENDOFFILE:
			raise errors.TokenMismatchError('Missing close parenthesis after Random operator...')
		elif token['type'] is TokenType.KEYWORD_ENDSCRIPT:
			if parenth_count > 0:
				raise errors.TokenMismatchError('Missing close parenthesis after Random operator...')
			break # @todo: verify
		elif token['type'] is TokenType.OPENPARENTH:
			parenth_count += 1
		elif token['type'] is TokenType.CLOSEPARENTH:
			if parenth_count > 0:
				parenth_count -= 1
			else:
				break
		elif is_token_type_random_keyword(token['type']):
			skip_random_operator(iterator)


# -------------------------------------------------------------------------------------------------
def get_random_operator_count(tokens):
	operator_count = 0
	parenth_count = 0
	iterator = iter(tokens)
	# @todo: skip whitespace
	for token in iterator:
		if is_token_type_random_keyword(token['type']):
			skip_random_operator(iterator)

		if token['type'] is TokenType.ENDOFFILE:
			raise errors.TokenMismatchError('Missing close parenthesis after Random operator...')
		elif token['type'] is TokenType.KEYWORD_ENDSCRIPT:
			if parenth_count > 0:
				raise errors.TokenMismatchError('Missing close parenthesis after Random operator...')
			break # @todo: verify
		elif token['type'] is TokenType.KEYWORD_AT:
			operator_count += 1
		elif token['type'] is TokenType.OPENPARENTH:
			parenth_count += 1
		elif token['type'] is TokenType.CLOSEPARENTH:
			if parenth_count > 0:
				parenth_count -= 1
			else:
				break
	return operator_count


# -------------------------------------------------------------------------------------------------
class Random:

	# ---------------------------------------------------------------------------------------------
	def __init__(self):
		self.parenth_count = 0
		self.offset_count = 0
		self.current_offset = 0
		self.weights_offset = 0
		self.weights = []
		self.offsets_offset = 0
		self.offsets = []


# -------------------------------------------------------------------------------------------------
class SwitchPointer:

	# @todo: Might not need a separate class for this? 

	# ---------------------------------------------------------------------------------------------
	def __init__(self):
		self.to_next = []
		self.to_end = []

	# ---------------------------------------------------------------------------------------------
	def set_to_next_pointer(self, offset):
		index = len(self.to_next)
		if index == 0:
			self.to_next.append({'current': offset, 'next': -1})
		else:
			self.to_next[index - 1]['next'] = ((offset - self.to_next[index - 1]['current']) - 2)
			self.to_next.append({'current': offset, 'next': -1})

	# ---------------------------------------------------------------------------------------------
	def set_to_end_pointer(self, offset):
		self.to_end.append({'current': offset, 'next': -1})

	# ---------------------------------------------------------------------------------------------
	def set_to_end_switch(self, offset):
		for p in self.to_end:
			p['next'] = (offset - p['current'])
		self.to_next[-1]['next'] = ((offset - self.to_next[-1]['current']) - 1)


# -------------------------------------------------------------------------------------------------
def calculate_if_jump_offset(offsets):
	if (offsets['else'] >= 0):
		return ((offsets['else'] + 2) - offsets['if'])
	elif (offsets['endif'] >= 0):
		return (offsets['endif'] - offsets['if'])
	else:
		return -1


# ---------------------------------------------------------------------------------------------
def calculate_else_jump_offset(offsets):
	if (offsets['endif'] >= 0):
		return (offsets['endif'] - offsets['else'])
	else:
		return 0


# -------------------------------------------------------------------------------------------------
class StringLineIterator:

	# ---------------------------------------------------------------------------------------------
	def __init__(self, inp):
		if isinstance(inp, str):
			self.lines = inp.splitlines()
		elif isinstance(inp, list) and all(isinstance(item, str) for item in inp):
			self.lines = inp
		else:
			raise TypeError('Input data must be a string or a list of strings')

	# ---------------------------------------------------------------------------------------------
	def __iter__(self):
		for index, line in enumerate(self.lines):
			yield index, line


# -------------------------------------------------------------------------------------------------
class LineIterator:

	# ---------------------------------------------------------------------------------------------
	def __init__(self, pathname):
		self.pathname = pathname

	# ---------------------------------------------------------------------------------------------
	def __iter__(self):
		with open(self.pathname, 'r') as file:
			for index, line in enumerate(file):
				yield index, line


# -------------------------------------------------------------------------------------------------
class QTokenIterator:

	# ---------------------------------------------------------------------------------------------
	token_misc_lookup_table = {
		'STARTSTRUCT': (TokenType.STARTSTRUCT, None),
		'ENDSTRUCT': (TokenType.ENDSTRUCT, None),
		'STARTARRAY': (TokenType.STARTARRAY, None),
		'ENDARRAY': (TokenType.ENDARRAY, None),
		'OPENPARENTH': (TokenType.OPENPARENTH, None),
		'CLOSEPARENTH': (TokenType.CLOSEPARENTH, None),
	}

	# ---------------------------------------------------------------------------------------------
	token_operator_lookup_table = {
		'EQUALS': (TokenType.EQUALS, None),
		'ASSIGN': (TokenType.ASSIGN, None),
		'DOT': (TokenType.DOT, None),
		'COMMA': (TokenType.COMMA, None),
		'COLON': (TokenType.COLON, None),
		'MINUS': (TokenType.MINUS, None),
		'ADD': (TokenType.ADD, None),
		'DIVIDE': (TokenType.DIVIDE, None),
		'MULTIPLY': (TokenType.MULTIPLY, None),
		'SHIFTRIGHT': (TokenType.OPERATOR_SHIFTRIGHT, None),
		'SHIFTLEFT': (TokenType.OPERATOR_SHIFTLEFT, None),
		'GREATERTHANEQUAL': (TokenType.GREATERTHANEQUAL, None),
		'LESSTHANEQUAL': (TokenType.LESSTHANEQUAL, None),
		'GREATERTHAN': (TokenType.GREATERTHAN, None),
		'LESSTHAN': (TokenType.LESSTHAN, None),
		'AT': (TokenType.KEYWORD_AT, None),
		'AND': (TokenType.OPERATOR_AND, None),
		'OR': (TokenType.OPERATOR_OR, None),
		'NOT': (TokenType.KEYWORD_NOT, None),
	}

	# ---------------------------------------------------------------------------------------------
	token_keyword_lookup_table = {
		'WHILE': (TokenType.KEYWORD_WHILE, None),
		'BEGIN': (TokenType.KEYWORD_WHILE, None),
		'REPEAT': (TokenType.KEYWORD_REPEAT, None),
		'BREAK': (TokenType.KEYWORD_BREAK, None),
		'SCRIPT': (TokenType.KEYWORD_SCRIPT, None),
		'ENDSCRIPT': (TokenType.KEYWORD_ENDSCRIPT, None),
		'IF': (TokenType.KEYWORD_IF, None),
		'ELSE': (TokenType.KEYWORD_ELSE, None),
		'ELSEIF': (TokenType.KEYWORD_ELSEIF, None),
		'ENDIF': (TokenType.KEYWORD_ENDIF, None),
		'RETURN': (TokenType.KEYWORD_RETURN, None),
		'RANDOMRANGE': (TokenType.KEYWORD_RANDOMRANGE, None),
		'RANDOMRANGE2': (TokenType.KEYWORD_RANDOMRANGE2, None),
		'RANDOM': (TokenType.KEYWORD_RANDOM, None),
		'RANDOM2': (TokenType.KEYWORD_RANDOM2, None),
		'RANDOMNOREPEAT': (TokenType.KEYWORD_RANDOMNOREPEAT, None),
		'RANDOMPERMUTE': (TokenType.KEYWORD_RANDOMNOREPEAT, None),
		'RANDOMSHUFFLE': (TokenType.KEYWORD_RANDOMPERMUTE, None),
		'NOT': (TokenType.KEYWORD_NOT, None),
		'AND': (TokenType.KEYWORD_AND, None),
		'OR': (TokenType.KEYWORD_OR, None),
		'SWITCH': (TokenType.KEYWORD_SWITCH, None),
		'ENDSWITCH': (TokenType.KEYWORD_ENDSWITCH, None),
		'CASE': (TokenType.KEYWORD_CASE, None),
		'DEFAULT': (TokenType.KEYWORD_DEFAULT, None),
		'NAN': (TokenType.FLOAT, float('nan')),
	}

	# ---------------------------------------------------------------------------------------------
	token_specs = [
		('INTERNAL_COMMENTBLOCKBEGIN', r'\/\*'), # Begin block comment `/*`
		('INTERNAL_COMMENTBLOCKEND', r'\*\/'), # End block comment `*/`
		('INTERNAL_COMMENTINLINE', r'(\/\/|#\/\/|;)[^\n]*'), # Inline comments starting with `//`, `#//`, or `;`

		('STARTSTRUCT', r'\{'),
		('ENDSTRUCT', r'\}'),
		('STARTARRAY', r'\['),
		('ENDARRAY', r'\]'),

		('EQUALS', r'=='), # Equality comparison
		('ASSIGN', r'='), # Assignment

		('INTERNAL_VECTOR', r'\(\-?[0-9]+(\.[0-9]+)?(,\s*\-?[0-9]+(\.[0-9]+)?)+\)'), # Matches simple vectors/pairs
		('OPENPARENTH', r'\('),
		('CLOSEPARENTH', r'\)'),

		('ALLARGS', r'<\.\.\.>'),
		('INTERNAL_ARGUMENTHEXCHECKSUM', r'<#"0x[0-9A-Fa-f]+">'),
		('INTERNAL_ARGUMENTSTRCHECKSUM', r'<#"[^"\n]*">'),
		('ARGUMENT', r'<[a-zA-Z_][a-zA-Z0-9_]*>'),

		('INTERNAL_INCLUDE', r'#INCLUDE\s+"[^"\n]+"'),
		('INTERNAL_RAW', r'#RAW\s+"[^"\n]+"'),
		('INTERNAL_DEFINE', r'#DEFINE\s+[a-zA-Z_][a-zA-Z0-9_]*'),
		('INTERNAL_IFDEF', r'#IFDEF\s+[a-zA-Z_][a-zA-Z0-9_]*'),
		('INTERNAL_IFNDEF', r'#IFNDEF\s+[a-zA-Z_][a-zA-Z0-9_]*'),
		('INTERNAL_GOTO', r'#GOTO\s+[a-zA-Z_][a-zA-Z0-9_]*'),
		('INTERNAL_HEXCHECKSUM', r'#"0x[0-9A-Fa-f]+?"'),
		('INTERNAL_STRCHECKSUM', r'#"[^"\n]*"'),

		('INTERNAL_ELSEDEF', r'#ELSE'),
		('INTERNAL_ENDIFDEF', r'#ENDIF'),

		('OR', r'\|\|'), # Logical OR
		('AND', r'&&'), # Logical AND
		('NOT', r'!'), # NOT

		('SHIFTRIGHT', r'>>'),
		('SHIFTLEFT', r'<<'),
		('GREATERTHANEQUAL', r'>='),
		('LESSTHANEQUAL', r'<='),
		('GREATERTHAN', r'>'),
		('LESSTHAN', r'<'),

		('STRING', r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\''), # Quoted strings with escaped quotes

		('FLOAT', r'-?\b\d+\.\d*|-?\.\d+\b'), # Matches floats with leading digits, or starting with a dot
		('INTEGER', r'-?\b\d+\b'), # Matches integers, possibly negative
		('HEXINTEGER', r'(?<!")0x[0-9A-Fa-f]+(?!")'),

		('ADD', r'\+'),
		('MINUS', r'(?<!\d)-(?!\d)'), # Negative lookahead and lookbehind to avoid matching negative numbers
		('MULTIPLY', r'\*'),
		('DIVIDE', r'\/'),
		('DOT', r'\.(?!\d)'),
		('AT', r'@'),
		('COMMA', r','),
		('COLON', r'::'),

		('INTERNAL_HASHTAG', r'#\w*'),
		('INTERNAL_LABEL', r'\b[a-zA-Z_][a-zA-Z0-9_]*:(?!:)'), # Jump label
		('INTERNAL_IDENTIFIER', r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'), # Identifiers

		('WHITESPACE', r'[ \t]+'), # Skip spaces and tabs
		('MISMATCH', r'.'), # Any other character
	]

	# ---------------------------------------------------------------------------------------------
	def __init__(self, lines, defines=[], level=0):

		# the level of nested files
		self.level = level
		# used for tracking #defined names
		self.defined_names = defines
		# keeps track of the current #ifdef scope(s)
		self.directive_stack_names = []
		# and whether we should skip parsing the lines or not
		self.directive_stack_active = [True]
		# used to determine if we should skip parsing commented lines
		self.skipping_block_comment = False
		# used by the iterator
		self.lines = lines
		# lexer regex 
		self.tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in QTokenIterator.token_specs)

	# ---------------------------------------------------------------------------------------------
	def __iter__(self):

		# @note: This method validates token types on a syntactical (micro) level only,
		# such as checking if the token type is recognized and can be parsed successfully.
		# Macro-level validations, including tracking of open braces and other structural 
		# considerations, should be performed by the calling function.

		previous_token_type = None

		for index, line in self.lines:

			stripped_line = line.strip()
			length_of_line = len(stripped_line)

			# skip empty lines...
			if not stripped_line:
				previous_token_type = None

			else:
				for mo in re.finditer(self.tok_regex, stripped_line, flags=re.IGNORECASE):

					kind, value = mo.lastgroup, mo.group()
					token_type, token_value = TokenType.KEYWORD_UNDEFINED, None

					if self.skipping_block_comment:
						if kind == 'INTERNAL_COMMENTBLOCKEND':
							self.skipping_block_comment = False
						continue # Ignore all tokens until block comment is closed
					elif kind == 'INTERNAL_COMMENTBLOCKBEGIN':
						self.skipping_block_comment = True
						continue
					elif kind == 'INTERNAL_COMMENTBLOCKEND':
						print(highlight_error_with_indicator(stripped_line, index, mo.start(), mo.end()))
						raise errors.InvalidFormatError('Unexpected `*/` without matching open block comment...')

					if kind not in ('INTERNAL_ELSEDEF', 'INTERNAL_ENDIFDEF', 'INTERNAL_IFDEF', 'INTERNAL_IFNDEF'):
						if not self.directive_stack_active[-1]:
							continue

					if kind == 'INTERNAL_VECTOR':
						try:
							result, count = extract_numbers_to_tuple(value)
							if count == 2:
								token_type, token_value = (TokenType.PAIR, result)
							elif count == 3:
								token_type, token_value = (TokenType.VECTOR, result)
							else:
								raise errors.InvalidFormatError(f'Unexpected number of elements found when parsing vector: {count} detected... {value}')
						except errors.InvalidFormatError as ex:
							print(highlight_error_with_indicator(stripped_line, index, mo.start(), mo.end()))
							raise ex

					elif kind == 'FLOAT':
						token_type, token_value = (TokenType.FLOAT, float(value))
					elif kind == 'INTEGER':
						token_type, token_value = (TokenType.INTEGER, int(value))
					elif kind == 'HEXINTEGER':
						token_type, token_value = (TokenType.HEXINTEGER, int(value, 0))

					elif kind == 'STRING':
						if value[0] == '\"':
							token_type, token_value = (TokenType.STRING, str(value[1:-1]))
						else:
							token_type, token_value = (TokenType.LOCALSTRING, str(value[1:-1]))

					elif kind in QTokenIterator.token_misc_lookup_table.keys():
						token_type, token_value = QTokenIterator.token_misc_lookup_table[kind]

					elif kind in QTokenIterator.token_operator_lookup_table.keys():
						token_type, token_value = QTokenIterator.token_operator_lookup_table[kind]

					elif kind == 'INTERNAL_HASHTAG':
						print(highlight_error_with_indicator(stripped_line, index, mo.start(), mo.end()))
						raise NotImplementedError(f'Unsupported hashtag `{value}` at line {index}...')

					elif kind == 'INTERNAL_IDENTIFIER':
						keyword = value.upper()
						if keyword in QTokenIterator.token_keyword_lookup_table.keys():
							token_type, token_value = QTokenIterator.token_keyword_lookup_table[keyword]
						else:
							token_type, token_value = (TokenType.NAME, (value, None))

					elif kind == 'INTERNAL_INCLUDE':
						token_type, token_value = (TokenType.INTERNAL_INCLUDE, value.split(' ')[1].replace('"', ''))
						if self.level > 0:
							includepath = Path(token_value).resolve()
							print(F'{Fore.YELLOW}WARNING: Only one level of file inclusion supported. Skipping "{includepath}"')
							previous_token_type = TokenType.ENDOFLINE # @hack
							continue
					elif kind == 'INTERNAL_RAW':
						token_type, token_value = (TokenType.INTERNAL_RAW, value.split(' ')[1])
						print(F'Parsing #raw with bytes `{token_value}`')

					elif kind == 'INTERNAL_DEFINE':
						token_type, token_value = (TokenType.INTERNAL_DEFINE, value.split(' ')[1])
						self.defined_names.append(token_value)
						continue

					elif kind == 'INTERNAL_IFDEF':
						token_type, token_value = (TokenType.INTERNAL_IFDEF, value.split(' ')[1])
						self.directive_stack_names.append(token_value)
						self.directive_stack_active.append(token_value in self.defined_names and self.directive_stack_active[-1])
						previous_token_type = TokenType.ENDOFLINE # @hack
						continue

					elif kind == 'INTERNAL_IFNDEF':
						token_type, token_value = (TokenType.INTERNAL_IFNDEF, value.split(' ')[1])
						self.directive_stack_names.append(token_value)
						self.directive_stack_active.append(token_value not in self.defined_names and self.directive_stack_active[-1])
						previous_token_type = TokenType.ENDOFLINE # @hack
						continue

					elif kind == 'INTERNAL_ELSEDEF':
						if not self.directive_stack_active or not self.directive_stack_names:
							print(highlight_error_with_indicator(stripped_line, index, mo.start(), mo.end()))
							raise errors.KeywordMismatchError('Unexpected `#else` keyword without matching `#ifdef`...')
						token_type, token_value = (TokenType.INTERNAL_ELSEDEF, self.directive_stack_names[-1])
						if self.directive_stack_active[-2]: # Check the second last item for the outer context's state
							self.directive_stack_active[-1] = not self.directive_stack_active[-1]
						previous_token_type = TokenType.ENDOFLINE # @hack
						continue

					elif kind == 'INTERNAL_ENDIFDEF':
						if not self.directive_stack_active or not self.directive_stack_names:
							print(highlight_error_with_indicator(stripped_line, index, mo.start(), mo.end()))
							raise errors.KeywordMismatchError('Unexpected `#endif` keyword without matching `#ifdef`...')
						self.directive_stack_active.pop()
						token_type, token_value = (TokenType.INTERNAL_ENDIFDEF, self.directive_stack_names.pop())
						previous_token_type = TokenType.ENDOFLINE # @hack
						continue

					elif kind == 'INTERNAL_GOTO':
						token_type, token_value = (TokenType.INTERNAL_GOTO, value.split(' ')[1])
					elif kind == 'INTERNAL_LABEL':
						token_type, token_value = (TokenType.INTERNAL_LABEL, value.split(':')[0])

					elif kind == 'INTERNAL_STRCHECKSUM':
						value = strip_hash_string_stuff(value)
						token_type, token_value = (TokenType.NAME, (value, None))
					elif kind == 'INTERNAL_HEXCHECKSUM':
						value = strip_hash_string_stuff(value)
						token_type, token_value = (TokenType.NAME, (None, int(value, 0)))

					elif kind == 'INTERNAL_ARGUMENTSTRCHECKSUM':
						value = strip_hash_string_stuff(strip_argument_string_stuff(value))
						token_type, token_value = (TokenType.ARGUMENT, (value, None))
					elif kind == 'INTERNAL_ARGUMENTHEXCHECKSUM':
						value = strip_hash_string_stuff(strip_argument_string_stuff(value))
						token_type, token_value = (TokenType.ARGUMENT, (None, int(value, 0)))

					elif kind == 'ARGUMENT':
						value = strip_argument_string_stuff(value)
						token_type, token_value = (TokenType.ARGUMENT, (value, None))
					elif kind == 'ALLARGS':
						token_type, token_value = (TokenType.ALLARGS, None)

					elif kind in ('INTERNAL_COMMENTINLINE', 'WHITESPACE', 'MISMATCH'):
						if kind == 'MISMATCH':
							print(highlight_error_with_indicator(stripped_line, index, mo.start(), mo.end()))
							raise NotImplementedError(f'Unexpected token `{value}` at line {index}....')
						continue # Skip spaces, newlines, and mismatches

					if token_type is TokenType.KEYWORD_UNDEFINED:
						print(highlight_error_with_indicator(stripped_line, index, mo.start(), mo.end()))
						raise NotImplementedError(f'The lexer token `{kind}` has not been handled properly...')

					previous_token_type = token_type

					yield {
						'type': token_type,
						'value': token_value,
						'index': index,
						'source': stripped_line,
						'start': mo.start(),
						'end': mo.end(),
					}

			# don't add a new line token if any of the following tokens was the previous one... 
			if previous_token_type not in (TokenType.ENDOFLINE, TokenType.INTERNAL_INCLUDE):
				previous_token_type = TokenType.ENDOFLINE
				yield {
					'type': TokenType.ENDOFLINE,
					'value': index,
					'index': index,
					'source': stripped_line,
					'start': length_of_line,
					'end': length_of_line + 1,
				}


# -------------------------------------------------------------------------------------------------
class QB:
	
	# ---------------------------------------------------------------------------------------------
	def __init__(self, params={}, defines=[]):

		# output byte stream
		self.stream = io.BytesIO()
		# checksum debug table
		self.checksums = {}
		# defined flags
		self.defines = [] + defines
		# q tokens
		self.tokens = []

		# @todo: Probably need to change this as we want different input and output parameters?
		# Right now the compiler will generate the bytes based on the input parameters anyways,
		# and the `to_file` method just dumps the bytes that have generated already...
		self.params = {
			'game': GameVersion.NONE,
			'debug': False
		} | params

	# ---------------------------------------------------------------------------------------------
	@classmethod
	def from_file(cls, filename, params={}, defines=[]):
		qb = cls(params, defines) # oaky
		pathname = Path(filename).resolve()
		extension = pathname.suffix.lower().strip('.')

		if not pathname.exists():
			raise FileNotFoundError(f'File does not exist... {pathname}')

		if extension == 'qb':
			raise NotImplementedError('Loading QB scripts is not supported yet...')
		elif extension == 'q':
			try:
				print('Compiling q script from file...', filename)
				source = LineIterator(pathname)
				qb.compile(source)
			except Exception as exeption:
				print(exeption)
				raise exeption
		return qb

	# ---------------------------------------------------------------------------------------------
	@classmethod
	def from_string(cls, string, params={}, defines=[]):
		qb = cls(params, defines) # oaky
		try:
			print('Compiling q script from string...')
			source = StringLineIterator(string)
			qb.compile(source)
		except Exception as exeption:
			print(exeption)
			raise exeption
		return qb

	# ---------------------------------------------------------------------------------------------
	def get_game_type(self):
		return self.params.get('game', GameVersion.NONE).value[0]

	# ---------------------------------------------------------------------------------------------
	def get_game_platform(self):
		return self.params.get('game', GameVersion.NONE).value[1]

	# ---------------------------------------------------------------------------------------------
	def compile(self, source):

		# -----------------------------------------------------------------------------------------
		# ìf are we debugging
		debug = self.params['debug']
		# shorthand for the end-of-line token to use in debug builds
		token_type_eol = TokenType.ENDOFLINENUMBER if debug else TokenType.ENDOFLINE

		# -----------------------------------------------------------------------------------------
		# if we are currently parsing tokens inside a script
		parsing_script = False
		# the name/checksum of the current script...
		current_script_name = None
		# for keeping track of open loops
		loop_count = 0
		# for keeping track of open parentheses
		parenth_count = 0
		# for keeping track of open structs/curly brackets
		script_curly_count = 0
		curly_count = 0
		# stores tuples of square, curly bracket counts... used for housekeeping
		curly_tracker = []
		# for keeping track of open arrays/square brackets
		square_count = 0
		script_square_count = 0
		# stores tuples of square, curly bracket counts... used for housekeeping
		square_tracker = []
		# for keeping track of if statements
		if_count = 0
		# housekeeping for if statements... 
		if_tracker = []
		# for keeping track of switch statements
		switch_case_expected = False
		# for keeping track of switch statements
		switch_count = 0
		# housekeeping for switch statements... 
		switch_tracker = []

		# for tracking randoms...
		random_count = 0
		random_tracker = []

		# -----------------------------------------------------------------------------------------
		if debug:
			print('\n---- compiler defines ----------')
			print(self.defines)

		# -----------------------------------------------------------------------------------------
		writer = BinaryWriter(self.stream)
		iterator = QTokenIterator(source, self.defines)

		# -----------------------------------------------------------------------------------------
		for token in iterator:
	
			# handle inclusion of other q files
			if token['type'] is TokenType.INTERNAL_INCLUDE:
				includepath = Path(token['value']).resolve()
				if includepath.is_file():
					print(F'Including file "{includepath}"')
					includesource = LineIterator(includepath)
					includeiterator = QTokenIterator(includesource, self.defines, level=1)
					# include all the new tokens in the list! assuming the tokenizer didn't fail...
					self.tokens.extend(includeiterator)
				else:
					# this is fine, as we want to include auto-generated files that may or may not exist...
					print(F'{Fore.YELLOW}WARNING: Could not include file "{includepath}"')
				continue # skip writing the internal include token byte to file...
			
			# write the normal tokens the list list
			self.tokens.append(token)

		# ---- write byte code --------------------------------------------------------------------
		for index, current_token in enumerate(self.tokens):
			current_token_type = current_token['type']

			# token may have been processed manually already,
			# or does not emit bytes in the current context...
			if current_token.get('skip', False):
				continue

			if current_token_type is TokenType.ENDOFLINE:
				writer.write_uint8(token_type_eol.value)
				if debug:
					writer.write_uint32(current_token['value'])

			elif current_token_type is TokenType.KEYWORD_SCRIPT:
				if parsing_script:
					print_token_error_message(current_token)
					raise errors.KeywordMismatchError("Unexpected `script` keyword while already inside a script at line...")
				next_token = self.tokens[index + 1]
				if next_token['type'] is not TokenType.NAME:
					print_token_error_message(next_token)
					raise errors.InvalidFormatError(F"Expected script name token `{TokenType.NAME}` but found `{next_token['type']}`...")

				parsing_script = True
				current_script_name = next_token['value']
				script_curly_count = curly_count
				script_square_count = square_count
				writer.write_uint8(TokenType.KEYWORD_SCRIPT.value)

			elif current_token_type is TokenType.KEYWORD_ENDSCRIPT:
				if not parsing_script:
					print_token_error_message(current_token)
					raise errors.KeywordMismatchError("Unexpected `endscript` keyword without matching script at line...")
				script_display_name = resolve_checksum_name_tuple(current_script_name)
				if loop_count > 0:
					print_token_error_message(current_token)
					raise errors.KeywordMismatchError(F"Missing `repeat` keyword in script `{script_display_name}`")
				if parenth_count != 0:
					print_token_error_message(current_token)
					raise errors.TokenMismatchError(F"Parentheses mismatch in script `{script_display_name}`")
				if script_curly_count > 0:
					if script_curly_count != curly_count:
						raise errors.TokenMismatchError(F"Curly bracket mismatch in script `{script_display_name}`")
						script_curly_count = 0
				if script_square_count > 0:
					if script_square_count != square_count:
						raise errors.TokenMismatchError(F"Square bracket mismatch in script `{script_display_name}`")
						script_square_count = 0
				parsing_script = False
				current_script_name = None
				writer.write_uint8(TokenType.KEYWORD_ENDSCRIPT.value)

			elif current_token_type is TokenType.KEYWORD_WHILE:
				if not parsing_script:
					print_token_error_message(current_token)
					raise errors.UnexpectedScopeError("`while` keyword can only be used inside scripts...")
				previous_token = self.tokens[index - 1]
				if previous_token['type'] is not TokenType.ENDOFLINE:
					print_token_error_message(current_token)
					raise errors.UnexpectedScopeError("`while` keyword must be the first word on its line...")
				loop_count += 1
				writer.write_uint8(TokenType.KEYWORD_WHILE.value)

			elif current_token_type is TokenType.KEYWORD_REPEAT:
				if not parsing_script:
					print_token_error_message(current_token)
					raise errors.UnexpectedScopeError("`repeat` keyword can only be used inside scripts...")
				if loop_count <= 0:
					print_token_error_message(current_token)
					raise errors.UnexpectedScopeError("`repeat` keyword can only be used with while loops...")
				previous_token = self.tokens[index - 1]
				if previous_token['type'] is not TokenType.ENDOFLINE:
					print_token_error_message(current_token)
					raise errors.UnexpectedScopeError("`repeat` keyword must be the first word on its line...")
				loop_count -= 1
				writer.write_uint8(TokenType.KEYWORD_REPEAT.value)

			elif current_token_type is TokenType.KEYWORD_BREAK:
				if not parsing_script:
					print_token_error_message(current_token)
					raise errors.UnexpectedScopeError("`break` keyword can only be used inside scripts...")
				if loop_count <= 0:
					print_token_error_message(current_token)
					raise errors.UnexpectedScopeError("`break` keyword can only be used inside while loops...")
				previous_token = self.tokens[index - 1]
				if previous_token['type'] is not TokenType.ENDOFLINE:
					print_token_error_message(current_token)
					raise errors.UnexpectedScopeError("`break` keyword must be the first word on its line...")
				writer.write_uint8(TokenType.KEYWORD_BREAK.value)

			elif current_token_type is TokenType.KEYWORD_RETURN:
				if not parsing_script:
					print_token_error_message(current_token)
					raise errors.UnexpectedScopeError("`return` keyword can only be used inside scripts...")
				previous_token = self.tokens[index - 1]
				if previous_token['type'] is not TokenType.ENDOFLINE:
					print_token_error_message(current_token)
					raise errors.UnexpectedScopeError("`return` keyword must be the first word on its line...")
				writer.write_uint8(TokenType.KEYWORD_RETURN.value)

			elif current_token_type is TokenType.STARTSTRUCT:
				curly_count += 1
				curly_tracker.append((square_count, curly_count))
				writer.write_uint8(TokenType.STARTSTRUCT.value)

			elif current_token_type is TokenType.ENDSTRUCT:
				if (curly_count < 1):
					print_token_error_message(current_token)
					raise errors.TokenMismatchError('Curly bracket mismatch!')
				if (curly_tracker[-1][0] != square_count):
					print_token_error_message(current_token)
					raise errors.TokenMismatchError('Square bracket mismatch!')
				curly_count -= 1
				curly_tracker.pop(curly_count)
				writer.write_uint8(TokenType.ENDSTRUCT.value)

			elif current_token_type is TokenType.STARTARRAY:
				square_count += 1
				square_tracker.append((square_count, curly_count))
				writer.write_uint8(TokenType.STARTARRAY.value)

			elif current_token_type is TokenType.ENDARRAY:
				if (square_count < 1):
					print_token_error_message(current_token)
					raise errors.TokenMismatchError('Square bracket mismatch!')
				if (square_tracker[-1][1] != curly_count):
					print_token_error_message(current_token)
					raise errors.TokenMismatchError('Curly bracket mismatch!')
				square_count -= 1
				square_tracker.pop(square_count)
				writer.write_uint8(TokenType.ENDARRAY.value)

			elif current_token_type is TokenType.OPENPARENTH:
				parenth_count += 1
				writer.write_uint8(TokenType.OPENPARENTH.value)

			elif current_token_type is TokenType.CLOSEPARENTH:
				parenth_count -= 1
				if random_count > 0:
					if (random_tracker[-1].parenth_count == parenth_count):
						if (random_tracker[-1].current_offset != random_tracker[-1].offset_count):
							raise errors.InvalidFormatError("Unexpected close parenthesis in Random operator...")
						# Make each of the jump commands at the end of each block jump to after the random operator.
						current_buffer_size = writer.stream.tell()
						for i in range(1, random_tracker[-1].offset_count):
							after_offset = (random_tracker[-1].offsets_offset + ((i + 1) * 4)) + random_tracker[-1].offsets[i]
							jump_offset = current_buffer_size - after_offset
							# @todo: check for long jump token
							if current_buffer_size < after_offset:
								raise errors.InvalidFormatError("WritePos less than afterJump...")
							writer.seek(after_offset - 4)
							writer.write_uint32(jump_offset)
						random_count -= 1
						random_tracker.pop()
						writer.seek(0, os.SEEK_END)
						continue
				writer.write_uint8(TokenType.CLOSEPARENTH.value)

			elif current_token_type is TokenType.KEYWORD_SWITCH:
				switch_count += 1
				writer.write_uint8(TokenType.KEYWORD_SWITCH.value)
				if self.get_game_type() >= GameType.THUG2:
					switch_tracker.append(SwitchPointer())
					switch_case_expected = True

			elif current_token_type in (TokenType.KEYWORD_CASE, TokenType.KEYWORD_DEFAULT):
				if switch_count <= 0:
					print_token_error_message(current_token)
					raise errors.UnexpectedScopeError("`{current_token_type}` keyword must be used inside a switch statement...")
				if self.get_game_type() >= GameType.THUG2:
					if switch_case_expected:
						writer.write_uint8(current_token_type.value)
						writer.write_uint8(TokenType.KEYWORD_SHORTJUMP.value)
						switch_tracker[-1].set_to_next_pointer(writer.stream.tell())
						writer.write_uint16(0x6969) # placeholder
						switch_case_expected = False
					else:
						writer.write_uint8(TokenType.KEYWORD_SHORTJUMP.value)
						switch_tracker[-1].set_to_end_pointer(writer.stream.tell())
						writer.write_uint16(0x6969) # placeholder
						writer.write_uint8(current_token_type.value)
						writer.write_uint8(TokenType.KEYWORD_SHORTJUMP.value)
						switch_tracker[-1].set_to_next_pointer(writer.stream.tell())
						writer.write_uint16(0x6969) # placeholder
				else:
					writer.write_uint8(current_token_type.value)

			elif current_token_type is TokenType.KEYWORD_ENDSWITCH:
				if switch_count <= 0:
					print_token_error_message(current_token)
					raise errors.KeywordMismatchError("Unexpected `endswitch` keyword without corresponding `switch`...")
				if switch_case_expected:
					print_token_error_message(current_token)
					raise errors.KeywordMismatchError("Unexpected `endswitch` without a `case`...")
				writer.write_uint8(current_token_type.value)
				if self.get_game_type() >= GameType.THUG2:
					switch_tracker[-1].set_to_end_switch(writer.stream.tell())
					for p in switch_tracker[-1].to_next:
						writer.seek(p['current'])
						writer.write_uint16(p['next'])
					for p in switch_tracker[-1].to_end:
						writer.seek(p['current'])
						writer.write_uint16(p['next'])
					switch_count -= 1
					switch_tracker.pop(switch_count)
					writer.seek(0, os.SEEK_END)
				else:
					switch_count -= 1

			elif current_token_type is TokenType.KEYWORD_IF:
				if not parsing_script:
					print_token_error_message(current_token)
					raise errors.UnexpectedScopeError("`if` keyword can only be used inside scripts...")
				previous_token = self.tokens[index - 1]
				if previous_token['type'] is not TokenType.ENDOFLINE:
					print_token_error_message(current_token)
					raise errors.UnexpectedScopeError("`if` keyword must be the first word on its line...")
				if_count += 1
				if self.get_game_type() >= GameType.THUG2:
					writer.write_uint8(TokenType.KEYWORD_IF2.value)
					if_tracker.append({'if': writer.stream.tell(), 'else': -1, 'endif': -1})
					writer.write_uint16(0x6969) # placeholder
				else:
					writer.write_uint8(TokenType.KEYWORD_IF.value)

			elif current_token_type is TokenType.KEYWORD_ELSE:
				# @todo: error checking
				if self.get_game_type() >= GameType.THUG2:
					writer.write_uint8(TokenType.KEYWORD_ELSE2.value)
					if_tracker[-1]['else'] = writer.stream.tell()
					writer.write_uint16(0x6969) # placeholder
				else:
					writer.write_uint8(TokenType.KEYWORD_ELSE.value)

			elif current_token_type is TokenType.KEYWORD_ELSEIF:
				if self.get_game_type() == GameType.THPG:
					print_token_error_message(current_token)
					raise NotImplementedError(F"Unsupported operator `{current_token_type}` for `{self.params['game']}`...")
				# @todo: implement? can use regular if and else tokens for the other games...

			elif current_token_type is TokenType.KEYWORD_ENDIF:
				# @todo: error checking
				if_count -= 1
				writer.write_uint8(current_token_type.value)
				if self.get_game_type() >= GameType.THUG2:
					if_tracker[if_count]['endif'] = writer.stream.tell()
					if if_tracker[if_count]['if'] >= 0:
						writer.seek(if_tracker[if_count]['if'])
						writer.write_uint16(calculate_if_jump_offset(if_tracker[if_count]))
						writer.seek(0, os.SEEK_END)
					if if_tracker[if_count]['else'] >= 0:
						writer.seek(if_tracker[if_count]['else'])
						writer.write_uint16(calculate_else_jump_offset(if_tracker[if_count]))
						writer.seek(0, os.SEEK_END)
					if_tracker.pop(if_count)

			elif current_token_type in (TokenType.OPERATOR_SHIFTRIGHT, TokenType.OPERATOR_SHIFTLEFT):
				print_token_error_message(current_token)
				raise NotImplementedError(F"Unsupported operator `{current_token_type}` for `{self.params['game']}`...")
				writer.write_uint8(current_token_type.value)

			elif current_token_type in (TokenType.GREATERTHANEQUAL, TokenType.LESSTHANEQUAL):
				if self.get_game_type() == GameType.THPG:
					print_token_error_message(current_token)
					raise NotImplementedError(F"Unsupported operator `{current_token_type}` for `{self.params['game']}`...")
				writer.write_uint8(current_token_type.value)

			# these are not supported in any games(?) – fallback to alternative tokens
			elif current_token_type is TokenType.KEYWORD_AND:
				writer.write_uint8(TokenType.OPERATOR_AND.value)
			elif current_token_type is TokenType.KEYWORD_OR:
				writer.write_uint8(TokenType.OPERATOR_OR.value)
			elif current_token_type is TokenType.EQUALS:
				writer.write_uint8(TokenType.ASSIGN.value)

			elif current_token_type is TokenType.ARGUMENT:
				writer.write_uint8(TokenType.ARGUMENT.value)
				writer.write_uint8(TokenType.NAME.value)
				checksum, name = resolve_checksum_tuple(current_token['value'])
				writer.write_uint32(checksum)
				if name:
					if not self.checksums.get(checksum):
						self.checksums[checksum] = name

			elif current_token_type is TokenType.ALLARGS:
				writer.write_uint8(TokenType.ALLARGS.value)

			elif current_token_type is TokenType.NAME:
				writer.write_uint8(TokenType.NAME.value)
				checksum, name = resolve_checksum_tuple(current_token['value'])
				writer.write_uint32(checksum)
				if name:
					if not self.checksums.get(checksum):
						self.checksums[checksum] = name

			elif current_token_type is TokenType.INTEGER:
				writer.write_uint8(TokenType.INTEGER.value)
				writer.write_int32(current_token['value'])

			elif current_token_type is TokenType.HEXINTEGER:
				writer.write_uint8(TokenType.INTEGER.value)
				writer.write_uint32(current_token['value'])

			elif current_token_type is TokenType.FLOAT:
				writer.write_uint8(TokenType.FLOAT.value)
				writer.write_float(current_token['value'])

			elif current_token_type is TokenType.PAIR:
				writer.write_uint8(TokenType.PAIR.value)
				writer.write_float(current_token['value'][0])
				writer.write_float(current_token['value'][1])

			elif current_token_type is TokenType.VECTOR:
				writer.write_uint8(TokenType.VECTOR.value)
				writer.write_float(current_token['value'][0])
				writer.write_float(current_token['value'][1])
				writer.write_float(current_token['value'][2])

			elif current_token_type in (TokenType.STRING, TokenType.LOCALSTRING):
				writer.write_uint8(current_token_type.value)
				writer.write_uint32(len(current_token['value']) + 1)
				writer.write_string(current_token['value'])
				writer.write_uint8(0)

			elif current_token_type in (TokenType.KEYWORD_RANDOMRANGE, TokenType.KEYWORD_RANDOMRANGE2):
				if not parsing_script:
					print_token_error_message(current_token)
					raise errors.UnexpectedScopeError("`RandomRange` keyword can only be used inside scripts...")
				next_token = self.tokens[index + 1]
				if next_token['type'] is not TokenType.PAIR:
					print_token_error_message(next_token)
					raise errors.InvalidFormatError(F"Expected `{TokenType.PAIR}` token proceeding `{current_token_type}`, but found `{next_token['type']}`...")
				writer.write_uint8(current_token_type.value)

			elif is_token_type_random_keyword(current_token_type):
				next_token = self.tokens[index + 1]
				if next_token['type'] is not TokenType.OPENPARENTH:
					print_token_error_message(next_token)
					raise errors.InvalidFormatError("Random keyword must be followed by an open parenthesis...")
				next_token['skip'] = True
				parenth_count += 1 # eh
				offset_count = get_random_operator_count(self.tokens[index + 1:])
				# Recording what the ParenthCount was at the time the Random keyword was encountered, hence the ParenthCount-1
				# (the random keyword is followed by an open parenth)
				# Recording the ParenthCount so that when a close parenth is encountered later we can tell whether
				# it is the close parenth of the random rather than of some sub expression by comparing counts.
				writer.write_uint8(current_token_type.value)
				writer.write_uint32(offset_count)

				ro = Random()
				ro.weights_offset = writer.stream.tell()
				if self.get_game_type() > GameType.THPS4:
					ro.offsets_offset = (ro.weights_offset + (offset_count * 2))
				else:
					ro.offsets_offset = ro.weights_offset
				ro.current_offset = 0
				ro.offset_count = offset_count
				ro.parenth_count = parenth_count - 1
				random_tracker.append(ro)
				random_count += 1
				if self.get_game_type() > GameType.THPS4:
					writer.write_bytes(b'\x69' * (offset_count * 2)) # placeholder for weights
				writer.write_bytes(b'\x69' * (offset_count * 4)) # placeholder for offsets

			elif current_token_type is TokenType.KEYWORD_AT:
				# @todo: error handling
				if (random_tracker[-1].current_offset > 0):
					writer.write_uint8(TokenType.JUMP.value)
					writer.write_uint32(0) # placeholder
				random_offset = (writer.stream.tell() - (random_tracker[-1].offsets_offset + ((random_tracker[-1].current_offset + 1) * 4)))
				writer.seek(random_tracker[-1].offsets_offset + (random_tracker[-1].current_offset * 4))
				writer.write_uint32(random_offset)
				random_tracker[-1].offsets.append(random_offset)
				if self.get_game_type() > GameType.THPS4:
					writer.seek(random_tracker[-1].weights_offset + (random_tracker[-1].current_offset * 2))
					writer.write_uint16(1) # idk?
				random_tracker[-1].weights.append(1)
				random_tracker[-1].current_offset += 1
				writer.seek(0, os.SEEK_END)

			elif current_token_type is TokenType.MULTIPLY:
				previous_token = self.tokens[index - 1]
				if previous_token['type'] is TokenType.KEYWORD_AT:
					weight_value = 0
					next_token = self.tokens[index + 1]
					if next_token['type'] is TokenType.INTEGER:
						next_token['skip'] = True
						weight_value = next_token['value']
					else:
						print_token_error_message(next_token)
						raise errors.InvalidFormatError("In the random operator, @* must be followed by an integer...")
					# @todo: validate
					if self.get_game_type() > GameType.THPS4:
						writer.seek(random_tracker[-1].weights_offset + ((random_tracker[-1].current_offset - 1) * 2))
						writer.write_uint16(weight_value) # idk?
					random_tracker[-1].weights[(random_tracker[-1].current_offset - 1)] = weight_value
					if (random_tracker[-1].current_offset == random_tracker[-1].offset_count):
						weight_sum = sum(random_tracker[-1].weights)
						if weight_sum <= 0:
							raise ValueError('The sum of the Random operator weight values must be greater than zero')
						if weight_sum > 32767:
							raise ValueError('The sum of the Random operator weight values is too large')
					writer.seek(0, os.SEEK_END)
					continue
				writer.write_uint8(current_token_type.value)

			else:
				# @note: dump all the remaining one-byte tokens here...
				# assuming that they don't require any extra housekeeping
				#print(F"Writing unhandled 8bit token `{current_token_type}`")
				writer.write_uint8(current_token_type.value)

		# ---- write debug table ------------------------------------------------------------------
		for checksum, name in self.checksums.items():
			writer.write_uint8(TokenType.CHECKSUM_NAME.value)
			writer.write_uint32(checksum)
			writer.write_string(name)
			writer.write_uint8(0)
	
		# ---- write end of file ------------------------------------------------------------------
		writer.write_uint8(TokenType.ENDOFFILE.value)
		writer.write_uint8(TokenType.ENDOFFILE.value) # ehh

		# ---- debugging --------------------------------------------------------------------------
		if debug:
			print('---- checksums -----------------')
			for checksum, name in self.checksums.items():
				print(F"{checksum:#010x} '{name}'")
			print('---- tokens --------------------')
			for token in self.tokens:
				print(token)

	# ---------------------------------------------------------------------------------------------
	def to_file(self, filename, params):
		pathname = Path(filename).resolve()
		if not self.stream:
			raise ValueError('The byte stream has no data!')
		#print(self.stream.getvalue().hex())
		with open(pathname, 'wb') as out:
			out.write(self.stream.getvalue())
		return True

	# ---------------------------------------------------------------------------------------------
	def to_console(self):
		if not self.stream:
			raise ValueError('The byte stream has no data!')
		print(self.stream.getvalue().hex())
		return True
