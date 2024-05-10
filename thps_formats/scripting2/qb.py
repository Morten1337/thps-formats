import os
import io
import re
import json
from collections import UserDict, UserList

from colorama import Fore, Back, Style
import colorama

from pathlib import Path as Path

from thps_formats.utils.writer import BinaryWriter
from thps_formats.shared.enums import GameType, GameVersion
from thps_formats.scripting2.enums import TokenType, ElementType
import thps_formats.scripting2.utils as qutils

import thps_formats.scripting2.error as error

# @warn: probably shouldnt have this here...
colorama.init(autoreset=False)

# --- todo ----------------------------------------------------------------------------------------
# - tokenizer->lexer->compiler
# - fix incorrect line numbers
# - improve error message handling


# -------------------------------------------------------------------------------------------------
def skip_random_operator(iterator):
	parenth_count = 1
	# @todo: skip whitespace
	next_token = next(iterator)
	if next_token['type'] is not TokenType.OPENPARENTH:
		raise error.InvalidFormatError("Random keyword must be followed by an open parenthesis...")

	for token in iterator:
		if qutils.is_token_type_random_keyword(token['type']):
			skip_random_operator(iterator)
		elif token['type'] is TokenType.ENDOFFILE:
			raise error.TokenMismatchError('Missing close parenthesis after Random operator...')
		elif token['type'] is TokenType.KEYWORD_ENDSCRIPT:
			if parenth_count > 0:
				raise error.TokenMismatchError('Missing close parenthesis after Random operator...')
			break # @todo: verify
		elif token['type'] is TokenType.OPENPARENTH:
			parenth_count += 1
		elif token['type'] is TokenType.CLOSEPARENTH:
			parenth_count -= 1
			if parenth_count == 0:
				break


# -------------------------------------------------------------------------------------------------
def get_random_operator_count(tokens):
	operator_count = 0
	parenth_count = 0
	iterator = iter(tokens)
	# @todo: skip whitespace
	for token in iterator:
		if qutils.is_token_type_random_keyword(token['type']):
			skip_random_operator(iterator)
		elif token['type'] is TokenType.ENDOFFILE:
			raise error.TokenMismatchError('Missing close parenthesis after Random operator...')
		elif token['type'] is TokenType.KEYWORD_ENDSCRIPT:
			if parenth_count > 0:
				raise error.TokenMismatchError('Missing close parenthesis after Random operator...')
			break # @todo: verify
		elif token['type'] is TokenType.KEYWORD_AT:
			operator_count += 1
		elif token['type'] is TokenType.OPENPARENTH:
			parenth_count += 1
		elif token['type'] is TokenType.CLOSEPARENTH:
			parenth_count -= 1
			if parenth_count == 0:
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
		'RANDOMPERMUTE': (TokenType.KEYWORD_RANDOMPERMUTE, None),
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

		('INTERNAL_VECTOR', r'\(\s*-?[0-9]*(\.[0-9]+)?(\s*,\s*-?[0-9]*(\.[0-9]+)?)+\s*\)'), # Matches simple vectors/pairs
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
			if stripped_line:

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
						print(error.highlight_error_with_indicator(stripped_line, index, mo.start(), mo.end()))
						raise error.InvalidFormatError('Unexpected `*/` without matching open block comment...')

					if kind not in ('INTERNAL_ELSEDEF', 'INTERNAL_ENDIFDEF', 'INTERNAL_IFDEF', 'INTERNAL_IFNDEF'):
						if not self.directive_stack_active[-1]:
							continue

					if kind == 'INTERNAL_VECTOR':
						try:
							result, count = qutils.extract_numbers_to_tuple(value)
							if count == 2:
								token_type, token_value = (TokenType.PAIR, result)
							elif count == 3:
								token_type, token_value = (TokenType.VECTOR, result)
							else:
								raise error.InvalidFormatError(F"Unexpected number of elements found when parsing vector: {count} detected... {value}")
						except error.InvalidFormatError as ex:
							print(error.highlight_error_with_indicator(stripped_line, index, mo.start(), mo.end()))
							raise ex

					elif kind == 'FLOAT':
						token_type, token_value = (TokenType.FLOAT, float(value))
					elif kind == 'INTEGER':
						token_type, token_value = (TokenType.INTEGER, int(value))
					elif kind == 'HEXINTEGER':
						token_type, token_value = (TokenType.HEXINTEGER, int(value, 0))

					elif kind == 'STRING':
						token_type, token_value = qutils.handle_string_stuff(value)

					elif kind in QTokenIterator.token_misc_lookup_table.keys():
						token_type, token_value = QTokenIterator.token_misc_lookup_table[kind]

					elif kind in QTokenIterator.token_operator_lookup_table.keys():
						token_type, token_value = QTokenIterator.token_operator_lookup_table[kind]

					elif kind == 'INTERNAL_HASHTAG':
						print(error.highlight_error_with_indicator(stripped_line, index, mo.start(), mo.end()))
						raise NotImplementedError(F"Unsupported hashtag `{value}` at line {index}...")

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
							error.print_warning_message(F"Only one level of file inclusion supported. Skipping '{includepath}'")
							previous_token_type = TokenType.ENDOFLINE # @hack
							continue
					elif kind == 'INTERNAL_RAW':
						token_type, token_value = (TokenType.INTERNAL_RAW, value.split(' ')[1])
						print(F"Parsing #raw with bytes `{token_value}`")
						continue

					elif kind == 'INTERNAL_DEFINE':
						token_type, token_value = (TokenType.INTERNAL_DEFINE, value.split(' ')[1])
						self.defined_names.append(token_value)
						previous_token_type = TokenType.ENDOFLINE # @hack
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
							print(error.highlight_error_with_indicator(stripped_line, index, mo.start(), mo.end()))
							raise error.KeywordMismatchError('Unexpected `#else` keyword without matching `#ifdef`...')
						token_type, token_value = (TokenType.INTERNAL_ELSEDEF, self.directive_stack_names[-1])
						if self.directive_stack_active[-2]: # Check the second last item for the outer context's state
							self.directive_stack_active[-1] = not self.directive_stack_active[-1]
						previous_token_type = TokenType.ENDOFLINE # @hack
						continue

					elif kind == 'INTERNAL_ENDIFDEF':
						if not self.directive_stack_active or not self.directive_stack_names:
							print(error.highlight_error_with_indicator(stripped_line, index, mo.start(), mo.end()))
							raise error.KeywordMismatchError('Unexpected `#endif` keyword without matching `#ifdef`...')
						self.directive_stack_active.pop()
						token_type, token_value = (TokenType.INTERNAL_ENDIFDEF, self.directive_stack_names.pop())
						previous_token_type = TokenType.ENDOFLINE # @hack
						continue

					elif kind == 'INTERNAL_GOTO':
						token_type, token_value = (TokenType.INTERNAL_GOTO, value.split(' ')[1])
					elif kind == 'INTERNAL_LABEL':
						token_type, token_value = (TokenType.INTERNAL_LABEL, value.split(':')[0])

					elif kind == 'INTERNAL_STRCHECKSUM':
						value = qutils.strip_hash_string_stuff(value)
						token_type, token_value = (TokenType.NAME, (value, None))
					elif kind == 'INTERNAL_HEXCHECKSUM':
						value = qutils.strip_hash_string_stuff(value)
						token_type, token_value = (TokenType.NAME, (None, int(value, 0)))

					elif kind == 'INTERNAL_ARGUMENTSTRCHECKSUM':
						value = qutils.strip_hash_string_stuff(qutils.strip_argument_string_stuff(value))
						token_type, token_value = (TokenType.ARGUMENT, (value, None))
					elif kind == 'INTERNAL_ARGUMENTHEXCHECKSUM':
						value = qutils.strip_hash_string_stuff(qutils.strip_argument_string_stuff(value))
						token_type, token_value = (TokenType.ARGUMENT, (None, int(value, 0)))

					elif kind == 'ARGUMENT':
						value = qutils.strip_argument_string_stuff(value)
						token_type, token_value = (TokenType.ARGUMENT, (value, None))
					elif kind == 'ALLARGS':
						token_type, token_value = (TokenType.ALLARGS, None)

					elif kind in ('INTERNAL_COMMENTINLINE', 'WHITESPACE', 'MISMATCH'):
						if kind == 'MISMATCH':
							print(error.highlight_error_with_indicator(stripped_line, index, mo.start(), mo.end()))
							raise NotImplementedError(F"Unexpected token `{value}` at line {index}....")
						continue # Skip spaces, newlines, and mismatches

					if token_type is TokenType.KEYWORD_UNDEFINED:
						print(error.highlight_error_with_indicator(stripped_line, index, mo.start(), mo.end()))
						raise NotImplementedError(F"The lexer token `{kind}` has not been handled properly...")

					previous_token_type = token_type

					yield {
						'type': token_type,
						'value': token_value,
						'index': index,
						'source': stripped_line,
						'start': mo.start(),
						'end': mo.end(),
					}

				else:

					# maybe add a newline token for empty lines
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
			raise FileNotFoundError(F"File does not exist... '{pathname}'")

		if extension == 'qb':
			raise NotImplementedError('Loading QB scripts is not supported yet...')
		elif extension == 'q':
			try:
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
		# if are we debugging
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
				if 'PYTEST_CURRENT_TEST' in os.environ:
					print(F"modifying include path '{token['value']}")
					token['value'] = token['value'].replace('..\\thugpro', 'tests\\data\\thugpro')

				includepath = Path(token['value']).resolve()
				if includepath.is_file():
					print(F"{Fore.GREEN}Including file '{includepath}'{Style.RESET_ALL}")
					includesource = LineIterator(includepath)
					includeiterator = QTokenIterator(includesource, self.defines, level=1)
					# include all the new tokens in the list! assuming the tokenizer didn't fail...
					self.tokens.extend(includeiterator)
				else:
					# this is fine, as we want to include auto-generated files that may or may not exist...
					error.print_warning_message(F"Could not include file '{includepath}'")
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
					error.print_token_error_message(current_token)
					raise error.KeywordMismatchError("Unexpected `script` keyword while already inside a script at line...")
				next_token = self.tokens[index + 1]
				if next_token['type'] is not TokenType.NAME:
					error.print_token_error_message(next_token)
					raise error.InvalidFormatError(F"Expected script name token `{TokenType.NAME}` but found `{next_token['type']}`...")

				parsing_script = True
				current_script_name = next_token['value']
				script_curly_count = curly_count
				script_square_count = square_count
				writer.write_uint8(TokenType.KEYWORD_SCRIPT.value)

			elif current_token_type is TokenType.KEYWORD_ENDSCRIPT:
				if not parsing_script:
					error.print_token_error_message(current_token)
					raise error.KeywordMismatchError("Unexpected `endscript` keyword without matching script at line...")
				script_display_name = qutils.resolve_checksum_name_tuple(current_script_name)
				if loop_count > 0:
					error.print_token_error_message(current_token)
					raise error.KeywordMismatchError(F"Missing `repeat` keyword in script `{script_display_name}`")
				if parenth_count != 0:
					error.print_token_error_message(current_token)
					raise error.TokenMismatchError(F"Parentheses mismatch in script `{script_display_name}`")
				if script_curly_count > 0:
					if script_curly_count != curly_count:
						raise error.TokenMismatchError(F"Curly bracket mismatch in script `{script_display_name}`")
						script_curly_count = 0
				if script_square_count > 0:
					if script_square_count != square_count:
						raise error.TokenMismatchError(F"Square bracket mismatch in script `{script_display_name}`")
						script_square_count = 0
				parsing_script = False
				current_script_name = None
				writer.write_uint8(TokenType.KEYWORD_ENDSCRIPT.value)

			elif current_token_type is TokenType.KEYWORD_WHILE:
				if not parsing_script:
					error.print_token_error_message(current_token)
					raise error.UnexpectedScopeError("`while` keyword can only be used inside scripts...")
				previous_token = self.tokens[index - 1]
				if previous_token['type'] is not TokenType.ENDOFLINE:
					error.print_token_error_message(current_token)
					raise error.UnexpectedScopeError("`while` keyword must be the first word on its line...")
				loop_count += 1
				writer.write_uint8(TokenType.KEYWORD_WHILE.value)

			elif current_token_type is TokenType.KEYWORD_REPEAT:
				if not parsing_script:
					error.print_token_error_message(current_token)
					raise error.UnexpectedScopeError("`repeat` keyword can only be used inside scripts...")
				if loop_count <= 0:
					error.print_token_error_message(current_token)
					raise error.UnexpectedScopeError("`repeat` keyword can only be used with while loops...")
				previous_token = self.tokens[index - 1]
				if previous_token['type'] is not TokenType.ENDOFLINE:
					error.print_token_error_message(current_token)
					raise error.UnexpectedScopeError("`repeat` keyword must be the first word on its line...")
				loop_count -= 1
				writer.write_uint8(TokenType.KEYWORD_REPEAT.value)

			elif current_token_type is TokenType.KEYWORD_BREAK:
				if not parsing_script:
					error.print_token_error_message(current_token)
					raise error.UnexpectedScopeError("`break` keyword can only be used inside scripts...")
				if loop_count <= 0:
					error.print_token_error_message(current_token)
					raise error.UnexpectedScopeError("`break` keyword can only be used inside while loops...")
				previous_token = self.tokens[index - 1]
				if previous_token['type'] is not TokenType.ENDOFLINE:
					error.print_token_error_message(current_token)
					raise error.UnexpectedScopeError("`break` keyword must be the first word on its line...")
				writer.write_uint8(TokenType.KEYWORD_BREAK.value)

			elif current_token_type is TokenType.KEYWORD_RETURN:
				if not parsing_script:
					error.print_token_error_message(current_token)
					raise error.UnexpectedScopeError("`return` keyword can only be used inside scripts...")
				previous_token = self.tokens[index - 1]
				if previous_token['type'] is not TokenType.ENDOFLINE:
					error.print_token_error_message(current_token)
					raise error.UnexpectedScopeError("`return` keyword must be the first word on its line...")
				writer.write_uint8(TokenType.KEYWORD_RETURN.value)

			elif current_token_type is TokenType.STARTSTRUCT:
				curly_count += 1
				curly_tracker.append((square_count, curly_count))
				writer.write_uint8(TokenType.STARTSTRUCT.value)

			elif current_token_type is TokenType.ENDSTRUCT:
				if (curly_count < 1):
					error.print_token_error_message(current_token)
					raise error.TokenMismatchError('Curly bracket mismatch!')
				if (curly_tracker[-1][0] != square_count):
					error.print_token_error_message(current_token)
					raise error.TokenMismatchError('Square bracket mismatch!')
				curly_count -= 1
				curly_tracker.pop(curly_count)
				writer.write_uint8(TokenType.ENDSTRUCT.value)

			elif current_token_type is TokenType.STARTARRAY:
				square_count += 1
				square_tracker.append((square_count, curly_count))
				writer.write_uint8(TokenType.STARTARRAY.value)

			elif current_token_type is TokenType.ENDARRAY:
				if (square_count < 1):
					error.print_token_error_message(current_token)
					raise error.TokenMismatchError('Square bracket mismatch!')
				if (square_tracker[-1][1] != curly_count):
					error.print_token_error_message(current_token)
					raise error.TokenMismatchError('Curly bracket mismatch!')
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
							error.print_token_error_message(current_token)
							raise error.InvalidFormatError("Unexpected close parenthesis in Random operator...")
						# Make each of the jump commands at the end of each block jump to after the random operator.
						current_buffer_size = writer.stream.tell()
						for i in range(1, random_tracker[-1].offset_count):
							after_offset = (random_tracker[-1].offsets_offset + ((i + 1) * 4)) + random_tracker[-1].offsets[i]
							jump_offset = current_buffer_size - after_offset
							# @todo: check for long jump token
							if current_buffer_size < after_offset:
								raise error.InvalidFormatError("WritePos less than afterJump...")
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
					error.print_token_error_message(current_token)
					raise error.UnexpectedScopeError(F"`{current_token_type}` keyword must be used inside a switch statement...")
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
					error.print_token_error_message(current_token)
					raise error.KeywordMismatchError("Unexpected `endswitch` keyword without corresponding `switch`...")
				if switch_case_expected:
					error.print_token_error_message(current_token)
					raise error.KeywordMismatchError("Unexpected `endswitch` without a `case`...")
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
					error.print_token_error_message(current_token)
					raise error.UnexpectedScopeError("`if` keyword can only be used inside scripts...")
				previous_token = self.tokens[index - 1]
				if previous_token['type'] is not TokenType.ENDOFLINE:
					error.print_token_error_message(current_token)
					raise error.UnexpectedScopeError("`if` keyword must be the first word on its line...")
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
					error.print_token_error_message(current_token)
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
				error.print_token_error_message(current_token)
				raise NotImplementedError(F"Unsupported operator `{current_token_type}` for `{self.params['game']}`...")
				writer.write_uint8(current_token_type.value)

			elif current_token_type in (TokenType.GREATERTHANEQUAL, TokenType.LESSTHANEQUAL):
				if self.get_game_type() == GameType.THPG:
					error.print_token_error_message(current_token)
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
				checksum, name = qutils.resolve_checksum_tuple(current_token['value'])
				writer.write_uint32(checksum)
				if name:
					if not self.checksums.get(checksum):
						self.checksums[checksum] = name

			elif current_token_type is TokenType.ALLARGS:
				writer.write_uint8(TokenType.ALLARGS.value)

			elif current_token_type is TokenType.NAME:
				writer.write_uint8(TokenType.NAME.value)
				checksum, name = qutils.resolve_checksum_tuple(current_token['value'])
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
				writer.write_string(current_token['value'], encoding='windows-1252')
				writer.write_uint8(0)

			elif current_token_type in (TokenType.KEYWORD_RANDOMRANGE, TokenType.KEYWORD_RANDOMRANGE2):
				if not parsing_script:
					error.print_token_error_message(current_token)
					raise error.UnexpectedScopeError("`RandomRange` keyword can only be used inside scripts...")
				next_token = self.tokens[index + 1]
				if next_token['type'] is not TokenType.PAIR:
					error.print_token_error_message(next_token)
					raise error.InvalidFormatError(F"Expected `{TokenType.PAIR}` token proceeding `{current_token_type}`, but found `{next_token['type']}`...")
				writer.write_uint8(current_token_type.value)

			elif qutils.is_token_type_random_keyword(current_token_type):
				next_token = self.tokens[index + 1]
				if next_token['type'] is not TokenType.OPENPARENTH:
					error.print_token_error_message(next_token)
					raise error.InvalidFormatError("Random keyword must be followed by an open parenthesis...")
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
						error.print_token_error_message(next_token)
						raise error.InvalidFormatError("In the random operator, @* must be followed by an integer...")
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

	# ---------------------------------------------------------------------------------------------
	def to_struct(self, resolve=False):

		script = False
		assignment = False
		keyname = None

		scope = QStruct()

		# parse tokens		
		for index, token in enumerate(self.tokens):
		
			if scope is None:
				raise ValueError("Scope is None!!!")

			token_type = token['type']

			if script and token_type is not TokenType.KEYWORD_ENDSCRIPT:
				continue

			if assignment:
				if not isinstance(scope, QStruct):
					raise TypeError("Unexpected scope type for value assignment!")
				if qutils.is_token_type_primitive(token_type):
					assignment = False
					scope[keyname] = QComponent.from_token(token)
				elif token_type is TokenType.STARTARRAY:
					assignment = False
					scope[keyname] = QArray(parent=scope)
					scope = scope[keyname]
				elif token_type is TokenType.STARTSTRUCT:
					assignment = False
					scope[keyname] = QStruct(parent=scope)
					scope = scope[keyname]

			elif isinstance(scope, QArray):
				if qutils.is_token_type_primitive(token_type):
					scope.append(QComponent.from_token(token))
				elif token_type in [TokenType.COMMA, TokenType.ENDOFLINE]:
					continue
				elif token_type is TokenType.STARTARRAY:
					scope.append(QArray(parent=scope))
					scope = scope[-1]
				elif token_type is TokenType.ENDARRAY:
					scope = scope.parent
				elif token_type is TokenType.STARTSTRUCT:
					scope.append(QStruct(parent=scope))
					scope = scope[-1]
				elif token_type is TokenType.ENDSTRUCT:
					raise Exception("Unexpected ENDSTRUCT with no matching STARTSTRUCT token!")
				else:
					raise NotImplementedError(F"Unexpected array token type! `{token_type}`")

			elif isinstance(scope, QStruct):
				if token_type is TokenType.NAME:
					# struct key name or global var name
					keyname = qutils.resolve_checksum_name_tuple(token['value'])
					scope[keyname] = None
				elif token_type is TokenType.ASSIGN:
					assignment = True
				elif token_type is TokenType.STARTSTRUCT:
					raise NotImplementedError("Unexpected STARTSTRUCT maybe function parameter?")
				elif token_type is TokenType.ENDSTRUCT:
					scope = scope.parent
				elif token_type is TokenType.STARTARRAY:
					raise NotImplementedError("Unexpected STARTARRAY maybe function parameters?")
				elif token_type is TokenType.ENDARRAY:
					raise Exception("Unexpected ENDARRAY with no matching STARTARRAY token!")
				elif token_type is TokenType.KEYWORD_SCRIPT:
					script = True
					scriptname = qutils.resolve_checksum_name_tuple(self.tokens[index + 1]['value'])
					scope[scriptname] = QComponent(None, ElementType.QSCRIPT)
				elif token_type is TokenType.KEYWORD_ENDSCRIPT:
					script = False

		# resolve references, ncomps structs etc...
		# @warn: only knows the current file scope!
		if resolve:
			scope.resolve_reference(scope)

		return scope

	# ---------------------------------------------------------------------------------------------
	def to_json(self, filename):
		pathname = Path(filename).resolve()
		if not self.stream:
			raise ValueError('The byte stream has no data!')
		root = self.to_struct(resolve=True)
		with open(pathname, 'w') as out:
			json.dump(root.to_json(), out, indent=4)
		return True


# @todo: review all the builtin methods and operators

# -------------------------------------------------------------------------------------------------
class QComponent:

	# ---------------------------------------------------------------------------------------------
	def __init__(self, _value=None, _type=ElementType.NONE):
		self.value = _value
		self.type = _type

	# ---------------------------------------------------------------------------------------------
	def __int__(self):
		# used for casting QComponent with ElementType.INTEGER to int
		if self.type is not ElementType.INTEGER:
			raise ValueError('QComponent must be INTEGER type!')
		return int(self.value)

	# ---------------------------------------------------------------------------------------------
	def __float__(self):
		# used for casting QComponent with ElementType.FLOAT to float
		if self.type is not ElementType.FLOAT:
			raise ValueError('QComponent must be FLOAT type!')
		return float(self.value)

	# ---------------------------------------------------------------------------------------------
	def __str__(self):
		# used for printing out in str messages
		return str(self.value)

	# ---------------------------------------------------------------------------------------------
	def __repr__(self):
		# used for printing out in json format
		if self.type is ElementType.INTEGER:
			return int(self.value)
		elif self.type is ElementType.FLOAT:
			return float(self.value)
		elif self.type is ElementType.NAME:
			return F"#{self.value}"
		elif self.type is ElementType.VECTOR:
			return F"({self.value[0]:.8f},{self.value[1]:.8f},{self.value[2]:.8f})"
		elif self.type is ElementType.PAIR:
			return F"({self.value[0]:.8f},{self.value[1]:.8f})"
		elif self.type is ElementType.QSCRIPT:
			return "<SCRIPT>"
		else:
			return str(self.value)

	# ---------------------------------------------------------------------------------------------
	def __hash__(self):
		# required for this type to appear in sets
		return id(self)

	# ---------------------------------------------------------------------------------------------
	# def __eq__(self, other):
	# 	if isinstance(other, QComponent):
	# 		return self.value == other.value
	# 	return self.value == other

	# ---------------------------------------------------------------------------------------------
	def to_json(self):
		return self.__repr__()

	# ---------------------------------------------------------------------------------------------
	@classmethod
	def from_token(cls, token):
		token_type = token['type']
		token_value = token['value']
		if token_type is TokenType.NAME:
			component = cls(qutils.resolve_checksum_name_tuple(token_value), ElementType.NAME)
		elif token_type is TokenType.INTEGER:
			component = cls(token_value, ElementType.INTEGER)
		elif token_type is TokenType.HEXINTEGER:
			component = cls(token_value, ElementType.INTEGER)
		elif token_type is TokenType.FLOAT:
			component = cls(token_value, ElementType.FLOAT)
		elif token_type is TokenType.PAIR:
			component = cls(token_value, ElementType.PAIR)
		elif token_type is TokenType.VECTOR:
			component = cls(token_value, ElementType.VECTOR)
		elif token_type is TokenType.LOCALSTRING:
			component = cls(token_value, ElementType.STRING)
		elif token_type is TokenType.STRING:
			component = cls(token_value, ElementType.STRING)
		else:
			component = cls(None, ElementType.NONE)
		return component


# -------------------------------------------------------------------------------------------------
class QStruct(UserDict):

	# ---------------------------------------------------------------------------------------------
	def __init__(self, parent=None):
		super().__init__()
		self.root = None # the root QStruct, used for looking up reference structs
		self.parent = parent # the parent QStruct or QArray
		self.mapping = {} # stores lowercase to original case key mapping
		self.references = {} # stores the keys that are references to other QStructs

	# ---------------------------------------------------------------------------------------------
	def __hash__(self):
		# required for this type to appear in sets
		return id(self)

	# ---------------------------------------------------------------------------------------------
	def __setitem__(self, key, value):
		# for setting local items with case-insensitive key
		if isinstance(key, str):
			lower_key = key.lower()
			if lower_key not in self.mapping:
				self.mapping[lower_key] = key
			super().__setitem__(self.mapping[lower_key], value)
		else:
			raise KeyError("Keys must be strings")

	# ---------------------------------------------------------------------------------------------
	def __getitem__(self, key):
		# for getting values with s[keyname]
		value = self._get_value(key)
		if value == 'NOTFOUND':
			raise KeyError(key)
		return value

	def get(self, key, default=None):
		# for getting values with s.get(keyname)
		value = self._get_value(key)
		return default if value == 'NOTFOUND' else value

	# ---------------------------------------------------------------------------------------------
	def __contains__(self, key):
		# check if case-insensitive key exists locally
		lower_key = key.lower()
		if lower_key in self.mapping:
			return True
		# recursively check referenced QStructs
		for ref_key in self.references.values():
			referenced_dict = self.root.get(ref_key, None)
			if referenced_dict and key in referenced_dict:
				return True
		return False

	# ---------------------------------------------------------------------------------------------
	def __delitem__(self, key):
		# delete item from local dict, case-insensitive key
		lower_key = key.lower()
		original_key = self.mapping.pop(lower_key, None)
		if original_key:
			super().__delitem__(original_key)
			self.references.pop(original_key, None)
		else:
			raise KeyError(key)

	# @todo: the following should probably return reference key and values too?

	# ---------------------------------------------------------------------------------------------
	def keys(self):
		return [self.mapping[k] for k in self.mapping]

	# ---------------------------------------------------------------------------------------------
	def values(self):
		return [self[self.mapping[k]] for k in self.mapping]

	# ---------------------------------------------------------------------------------------------
	def items(self):
		return [(k, self[k]) for k in self.keys()]

	# ---------------------------------------------------------------------------------------------
	def _get_value(self, key):
		# check if any referenced QStruct contains the key
		for ref_key in self.references.values():
			referenced_dict = self.root.get(ref_key, None)
			if referenced_dict and key in referenced_dict:
				return referenced_dict[key] # return value if key is found
		# if not found in any references, check local data
		lower_key = key.lower()
		original_key = self.mapping.get(lower_key, None)
		if original_key and original_key in self.data:
			return self.data[original_key]
		# @warn: None is a valid value for flags or references,
		# you should use `__contains__` to check for the existence of flags!
		return 'NOTFOUND'

	# ---------------------------------------------------------------------------------------------
	def _add_reference(self, key, reference_key):
		# internal function for keeping track of reference structs
		lower_key = key.lower()
		original_key = self.mapping.get(lower_key, key)
		self.references[original_key] = reference_key

	# ---------------------------------------------------------------------------------------------
	def resolve_reference(self, root):
		# @todo: This does not recognize hex checksum and names as the same,
		# so `test` and `#0x278081f3` will be treated as two separate entries...
		# @todo: Does not resolve assignment names, like profile = random_male_profile
		self.root = root
		for key, value in self.items():
			if value is None and key in root:
				self._add_reference(key, key)
			elif isinstance(value, (QStruct, QArray)):
				value.resolve_reference(root)

	# ---------------------------------------------------------------------------------------------
	def to_json(self):
		struct = {}
		for attr, value in self.data.items():
			if isinstance(value, (QStruct, QArray, QComponent)):
				struct[attr] = value.to_json()
			else:
				struct[attr] = value
		return struct


# -------------------------------------------------------------------------------------------------
class QArray(UserList):

	# ---------------------------------------------------------------------------------------------
	def __init__(self, data=[], parent=None):
		super().__init__(data)
		self.parent = parent

	# ---------------------------------------------------------------------------------------------
	def resolve_reference(self, root):
		for value in self.data:
			# if isinstance(value, QComponent):
			# 	if value.type is ElementType.NAME and value.value is None:
			# 		print('WARNING: Array element may be a reference?')
			if isinstance(value, QStruct):
				value.resolve_reference(root)

	# ---------------------------------------------------------------------------------------------
	def to_json(self):
		array = []
		for value in self.data:
			if isinstance(value, (QStruct, QArray, QComponent)):
				array.append(value.to_json())
			else:
				array.append(value)
		return array
