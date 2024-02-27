import io
import re

import colorama
from colorama import Fore, Style

from pathlib import Path as Path

from thps_formats.utils.writer import BinaryWriter
from thps_formats.shared.enums import GameType, GameVersion, PlatformType
from . enums import TokenType
from . crc32 import crc32_generate

# @warn: probably shouldnt have this here...
colorama.init(autoreset=True)

# --- todo ----------------------------------------------------------------------------------------
# - tokenizer->lexer->compiler
# - token post-processing
# 	- Script, Arrays, Structs, Parentheses - scopes
# 	- Random, RandomRange
# 	- Jumps, Ifs
# - actually generate bytes
# - #include directive
# - #raw bytes
# - fix incorrect line numbers
# - improve error message handling


# -------------------------------------------------------------------------------------------------
def print_token_error_message(token):
	print(highlight_error_with_indicator(token['source'], token['index'], token['start'], token['end']))


# -------------------------------------------------------------------------------------------------
def highlight_error_with_indicator(line, line_number, start_index, end_index):
	"""
	Highlights an error in a given line of code, prefixes it with a line number, and
	creates a visual indicator pointing to the start of the error in the line below.
	
	Args:
	- line (str): The line of code.
	- line_number (int): The line number to prefix.
	- start_index (int): The start index of the error in the line.
	- end_index (int): The end index of the error in the line.
	
	Returns:
	- str: Formatted string with the line, error highlighted, and visual indicator below.
	"""
	# Highlight the error within the line
	highlighted_line = insert_color_and_reset(line, Fore.RED, start_index, end_index)
	
	# Prefix the line number
	line_with_number = f'{Fore.CYAN}{line_number:4}| {Style.RESET_ALL}{highlighted_line}'
	
	# Create the error indicator line
	# Uses spaces to align with the start of the error, then a dash line, ending with an arrow
	indicator_line = ' ' * (6 + start_index) + Fore.RED + '^' * (end_index - start_index) + Style.RESET_ALL
	
	return f'Error:\n{line_with_number}\n{indicator_line}'


# -------------------------------------------------------------------------------------------------
def highlight_error_in_line(line, line_number, start_index, end_index):
	"""
	Highlights an error in a given line of code and prefixes it with a line number.
	
	Args:
	- line (str): The line of code.
	- line_number (int): The line number to prefix.
	- start_index (int): The start index of the error in the line.
	- end_index (int): The end index of the error in the line.
	
	Returns:
	- str: The line with the error highlighted and prefixed with the line number.
	"""
	# Highlight the error within the line
	highlighted_line = insert_color_and_reset(line, Fore.RED, start_index, end_index)
	
	# Prefix the line number
	line_with_number = f'{Fore.CYAN}{line_number:4}| {Style.RESET_ALL}{highlighted_line}'
	
	return line_with_number


# -------------------------------------------------------------------------------------------------
def insert_color_and_reset(text, color, start_index, end_index):
	"""
	Inserts a color at a specific index in a text and resets the color at another index.
	"""
	return text[:start_index] + color + text[start_index:end_index] + Style.RESET_ALL + text[end_index:]


# -------------------------------------------------------------------------------------------------
def extract_numbers_to_tuple(value):
	stripped_string = re.sub(r'[^\d,.-]', '', value)
	segments = stripped_string.split(',')
	# Use list comprehension to process segments
	numbers = [float(segment) for segment in segments if re.fullmatch(r'^-?\d*\.\d+$', segment) or re.fullmatch(r'^-?\d+$', segment)]
	# Identify invalid segments
	invalid_numbers = [segment for segment in segments if not (re.fullmatch(r'^-?\d*\.\d+$', segment) or re.fullmatch(r'^-?\d+$', segment)) and segment]
	if invalid_numbers:
		# @todo: print line number and code snippet
		raise InvalidFormatError(f'Unable to parse one or more numbers in the vector... {invalid_numbers}')
	return tuple(numbers), len(numbers)


# -------------------------------------------------------------------------------------------------
def tohex(val, nbits):
	return hex((val + (1 << nbits)) % (1 << nbits))


# -------------------------------------------------------------------------------------------------
def parse_checksum(value):
	value = value.lower().strip()
	if value.startswith('0x'):
		return int(value, 0)
	else:
		return int(value)


# -------------------------------------------------------------------------------------------------
def parse_checksum_name(value):
	pass


# -------------------------------------------------------------------------------------------------
def strip_hash_string_stuff(value):
	return value[2:-1] # #"hello" -> hello


# -------------------------------------------------------------------------------------------------
def strip_argument_string_stuff(value):
	return value[1:-1] # <hello> -> hello


# -------------------------------------------------------------------------------------------------
def resolve_checksum_name_tuple(value):

	if value[0] is not None:
		return value[0]

	if value[1] is not None and isinstance(value[1], int):
		# @todo: lookup name from table 
		return F"{value[1]:#010x}"

	raise ValueError('Trying to resolve checksum name, but no name or checksum was passed...')


# -------------------------------------------------------------------------------------------------
def resolve_checksum_tuple(value):

	# ('Name', 0xA1DC81F9)
	# (None, 0xa1dc81f9)
	# ('Name', None)

	if value[0] is not None:
		checksum = crc32_generate(value[0])
		print(F"Resolving checksum {checksum:#010x}")
		return checksum

	if value[1] is not None and isinstance(value[1], int):
		checksum = value[1]
		print(F"Resolving checksum {checksum:#010x}")
		return checksum

	raise ValueError('Trying to resolve checksum, but no name or checksum was passed...')


# -------------------------------------------------------------------------------------------------
class InvalidFormatError(Exception):
	pass


# -------------------------------------------------------------------------------------------------
class InvalidTokenError(Exception):
	pass


# -------------------------------------------------------------------------------------------------
class BracketMismatchError(Exception):
	pass


# -------------------------------------------------------------------------------------------------
class ContextualSyntaxError(Exception):
	pass


# -------------------------------------------------------------------------------------------------
class StringLineIterator:
	def __init__(self, inp):
		if isinstance(inp, str):
			self.lines = inp.splitlines()
		elif isinstance(inp, list) and all(isinstance(item, str) for item in inp):
			self.lines = inp
		else:
			raise TypeError('Input data must be a string or a list of strings')

	def __iter__(self):
		for index, line in enumerate(self.lines):
			yield index, line


# -------------------------------------------------------------------------------------------------
class LineIterator:

	def __init__(self, pathname):
		self.pathname = pathname

	def __iter__(self):
		with open(self.pathname, 'r') as file:
			for index, line in enumerate(file):
				yield index, line


# -------------------------------------------------------------------------------------------------
class QTokenIterator:

	# ---------------------------------------------------------------------------------------------
	def __init__(self, lines, defines=[]):

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

		self.token_misc_lookup_table = {
			'STARTSTRUCT': (TokenType.STARTSTRUCT, None),
			'ENDSTRUCT': (TokenType.ENDSTRUCT, None),
			'STARTARRAY': (TokenType.STARTARRAY, None),
			'ENDARRAY': (TokenType.ENDARRAY, None),
			'OPENPARENTH': (TokenType.OPENPARENTH, None),
			'CLOSEPARENTH': (TokenType.CLOSEPARENTH, None),
		}

		self.token_operator_lookup_table = {
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
		}

		self.token_keyword_lookup_table = {
			'WHILE': (TokenType.KEYWORD_WHILE, None),
			'BEGIN': (TokenType.KEYWORD_WHILE, None),
			'REPEAT': (TokenType.KEYWORD_REPEAT, None),
			'BREAK': (TokenType.KEYWORD_BREAK, None),
			'SCRIPT': (TokenType.KEYWORD_SCRIPT, None),
			'ENDSCRIPT': (TokenType.KEYWORD_ENDSCRIPT, None),
			'IF': (TokenType.KEYWORD_IF, None),
			'DOIF': (TokenType.KEYWORD_IF, None),
			'ELSE': (TokenType.KEYWORD_IF, None),
			'DOELSE': (TokenType.KEYWORD_ELSE, None),
			'ELSEIF': (TokenType.KEYWORD_ELSE, None),
			'DOELSEIF': (TokenType.KEYWORD_ELSE, None),
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
			'UNDEFINED': (TokenType.KEYWORD_UNDEFINED, None),
			'NAN': (TokenType.FLOAT, float('nan')),
		}

		self.token_specs = [
			('INTERNAL_COMMENTBLOCKBEGIN', r'\/\*'), # Begin block comment `/*`
			('INTERNAL_COMMENTBLOCKEND', r'\*\/'), # End block comment `*/`
			('INTERNAL_COMMENTINLINE', r'(\/\/|;)[^\n]*'), # Inline comments starting with `//` or `;`

			('STARTSTRUCT', r'\{'),
			('ENDSTRUCT', r'\}'),
			('STARTARRAY', r'\['),
			('ENDARRAY', r'\]'),

			('EQUALS', r'=='), # Equality comparison
			('ASSIGN', r'='), # Assignment

			('INTERNAL_VECTOR', r'\(([^\(\)]*,[^\(\)]*,?[^\(\)]*)\)'), # Matches simple vectors/pairs
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
		self.tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in self.token_specs)

	# ---------------------------------------------------------------------------------------------
	def __iter__(self):

		# @note: This method validates token types on a syntactical (micro) level only,
		# such as checking if the token type is recognized and can be parsed successfully.
		# Macro-level validations, including tracking of open braces and other structural 
		# considerations, should be performed by the calling function.

		previous_token_type = TokenType.KEYWORD_UNDEFINED

		for index, line in self.lines:

			stripped_line = line.strip()
			length_of_line = len(stripped_line)

			# skipping whitespace...
			if not stripped_line:
				continue

			for mo in re.finditer(self.tok_regex, stripped_line, flags=re.IGNORECASE):

				# @todo: should not re-use these for return data  
				kind = mo.lastgroup
				value = mo.group()

				if self.skipping_block_comment:
					if kind == 'INTERNAL_COMMENTBLOCKEND':
						self.skipping_block_comment = False
					continue # Ignore all tokens until block comment is closed
				elif kind == 'INTERNAL_COMMENTBLOCKBEGIN':
					self.skipping_block_comment = True
					continue

				if kind != 'INTERNAL_ELSEDEF' and kind != 'INTERNAL_ENDIFDEF':
					if not self.directive_stack_active[-1]:
						continue

				if kind == 'INTERNAL_VECTOR':
					try:
						result, count = extract_numbers_to_tuple(value)
						if count == 2:
							kind, value = (TokenType.PAIR, result)
						elif count == 3:
							kind, value = (TokenType.VECTOR, result)
						else:
							raise InvalidFormatError(f'Unexpected number of elements found when parsing vector: {count} detected... {value}')
					except InvalidFormatError as ex:
						print(highlight_error_with_indicator(stripped_line, index, mo.start(), mo.end()))
						raise ex

				elif kind == 'FLOAT':
					kind, value = (TokenType.FLOAT, float(value))
				elif kind == 'INTEGER':
					kind, value = (TokenType.INTEGER, int(value))
				elif kind == 'HEXINTEGER':
					kind, value = (TokenType.INTEGER, int(value, 0))

				elif kind == 'STRING':
					if value[0] == '\"':
						kind, value = (TokenType.STRING, str(value[1:-1]))
					else:
						kind, value = (TokenType.LOCALSTRING, str(value[1:-1]))

				elif kind in self.token_misc_lookup_table.keys():
					kind, value = self.token_misc_lookup_table.get(kind) 

				elif kind in self.token_operator_lookup_table.keys():
					kind, value = self.token_operator_lookup_table.get(kind) 

				elif kind == 'INTERNAL_HASHTAG':
					print(highlight_error_with_indicator(stripped_line, index, mo.start(), mo.end()))
					raise NotImplementedError(f'Unsupported hashtag `{value}` at line {index}...')

				elif kind == 'INTERNAL_IDENTIFIER':
					keyword = value.upper()
					if keyword in self.token_keyword_lookup_table.keys():
						kind, value = self.token_keyword_lookup_table.get(keyword)
					else:
						kind, value = (TokenType.NAME, (value, None))

				elif kind == 'INTERNAL_INCLUDE':
					kind, value = (TokenType.INTERNAL_INCLUDE, value.split(' ')[1])
					print(F'Parsing #include with path `{value}`')
				elif kind == 'INTERNAL_RAW':
					kind, value = (TokenType.INTERNAL_RAW, value.split(' ')[1])
					print(F'Parsing #raw with bytes `{value}`')

				elif kind == 'INTERNAL_DEFINE':
					kind, value = (TokenType.INTERNAL_DEFINE, value.split(' ')[1])
					self.defined_names.append(value)
					continue

				elif kind == 'INTERNAL_IFDEF':
					kind, value = (TokenType.INTERNAL_IFDEF, value.split(' ')[1])
					self.directive_stack_names.append(value)
					self.directive_stack_active.append(value in self.defined_names and self.directive_stack_active[-1])
					continue

				elif kind == 'INTERNAL_IFNDEF':
					kind, value = (TokenType.INTERNAL_IFNDEF, value.split(' ')[1])
					self.directive_stack_names.append(value)
					self.directive_stack_active.append(value not in self.defined_names and self.directive_stack_active[-1])
					continue

				elif kind == 'INTERNAL_ELSEDEF':
					kind, value = (TokenType.INTERNAL_ELSEDEF, self.directive_stack_names[-1])
					if self.directive_stack_active[-2]: # Check the second last item for the outer context's state
						self.directive_stack_active[-1] = not self.directive_stack_active[-1]
					continue

				elif kind == 'INTERNAL_ENDIFDEF':
					self.directive_stack_active.pop()
					kind, value = (TokenType.INTERNAL_ENDIFDEF, self.directive_stack_names.pop())
					continue

				elif kind == 'INTERNAL_GOTO':
					kind, value = (TokenType.INTERNAL_GOTO, value.split(' ')[1])
				elif kind == 'INTERNAL_LABEL':
					kind, value = (TokenType.INTERNAL_LABEL, value.split(':')[0])

				elif kind == 'INTERNAL_STRCHECKSUM':
					_value = strip_hash_string_stuff(value)
					kind, value = (TokenType.NAME, (_value, None))
				elif kind == 'INTERNAL_HEXCHECKSUM':
					_value = strip_hash_string_stuff(value)
					kind, value = (TokenType.NAME, (None, int(_value, 0)))

				elif kind == 'INTERNAL_ARGUMENTSTRCHECKSUM':
					_value = strip_hash_string_stuff(strip_argument_string_stuff(value))
					kind, value = (TokenType.ARGUMENT, (_value, None))
				elif kind == 'INTERNAL_ARGUMENTHEXCHECKSUM':
					_value = strip_hash_string_stuff(strip_argument_string_stuff(value))
					kind, value = (TokenType.ARGUMENT, (None, int(_value, 0)))

				elif kind == 'ARGUMENT':
					kind, value = (TokenType.ARGUMENT, (value, None))
				elif kind == 'ALLARGS':
					kind, value = (TokenType.ALLARGS, None)

				elif kind in ('INTERNAL_COMMENTINLINE', 'WHITESPACE', 'MISMATCH'):
					if kind == 'MISMATCH':
						print(highlight_error_with_indicator(stripped_line, index, mo.start(), mo.end()))
						raise NotImplementedError(f'Unexpected token `{value}` at line {index}....')
					continue # Skip spaces, newlines, and mismatches

				if type(kind) != TokenType:
					print(highlight_error_with_indicator(stripped_line, index, mo.start(), mo.end()))
					raise NotImplementedError(f'The lexer token `{kind}` has not been handled properly...')

				previous_token_type = kind

				yield {
					'type': kind,
					'value': value,
					'index': index,
					'source': stripped_line,
					'start': mo.start(),
					'end': mo.end(),
				}

			if previous_token_type is not TokenType.ENDOFLINE:
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

	# output byte stream
	stream = None
	# checksum debug table
	checksums = []
	# defined flags
	defines = []
	# q tokens
	tokens = []

	# @todo: Probably need to change this as we want different input and output parameters?
	# Right now the compiler will generate the bytes based on the input parameters anyways,
	# and the `to_file` method just dumps the bytes that have generated already...
	params = {
		'game': GameVersion.NONE,
		'debug': True,
	}

	# ---------------------------------------------------------------------------------------------
	def __init__(self, params={}, defines=[]):
		self.stream = io.BytesIO()
		self.defines.extend(defines)
		self.params.update(params)

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
				print('Compiling q script from file...')
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
		curly_count = 0
		script_curly_count = 0
		# stores tuples of square, curly bracket counts... used for housekeeping
		curly_tracker = []
		# for keeping track of open arrays/square brackets
		square_count = 0
		script_square_count = 0
		# stores tuples of square, curly bracket counts... used for housekeeping
		square_tracker = []

		# -----------------------------------------------------------------------------------------
		if debug:
			print('\n---- compiler defines ----------')
			print(self.defines)

		# -----------------------------------------------------------------------------------------
		writer = BinaryWriter(self.stream)
		iterator = QTokenIterator(source, self.defines)

		# -----------------------------------------------------------------------------------------
		for token in iterator:
			self.tokens.append(token)

		# -----------------------------------------------------------------------------------------
		for index, current_token in enumerate(self.tokens):
			current_token_type = current_token['type']
			if current_token_type is TokenType.ENDOFLINE:
				writer.write_uint8(token_type_eol.value)
				if debug:
					writer.write_uint32(current_token['value'])
				continue

			elif current_token_type is TokenType.KEYWORD_SCRIPT:
				if parsing_script:
					print_token_error_message(current_token)
					raise InvalidFormatError("Unexpected `script` keyword while already inside a script at line...")
				next_token = self.tokens[index + 1]
				if next_token['type'] is not TokenType.NAME:
					print_token_error_message(next_token)
					raise InvalidFormatError(F"Expected script name but found `{next_token['type']}`...")

				parsing_script = True
				current_script_name = next_token['value']
				script_curly_count = curly_count
				script_square_count = square_count
				writer.write_uint8(TokenType.KEYWORD_SCRIPT.value)
				continue

			elif current_token_type is TokenType.KEYWORD_ENDSCRIPT:
				if not parsing_script:
					print_token_error_message(current_token)
					raise InvalidFormatError("Unexpected `endscript` keyword without matching script at line...")
				script_display_name = resolve_checksum_name_tuple(current_script_name)
				if loop_count > 0:
					print_token_error_message(current_token)
					raise Exception(F"Missing `repeat` keyword in script `{script_display_name}`")
				if parenth_count != 0:
					print_token_error_message(current_token)
					raise BracketMismatchError(F"Parentheses mismatch in script `{script_display_name}`")
				if script_curly_count > 0:
					if script_curly_count != curly_count:
						raise BracketMismatchError(F"Curly bracket mismatch in script `{script_display_name}`")
						script_curly_count = 0
				if script_square_count > 0:
					if script_square_count != square_count:
						raise BracketMismatchError(F"Square bracket mismatch in script `{script_display_name}`")
						script_square_count = 0
				parsing_script = False
				current_script_name = None
				writer.write_uint8(TokenType.KEYWORD_ENDSCRIPT.value)
				continue

			elif current_token_type is TokenType.KEYWORD_WHILE:
				if not parsing_script:
					print_token_error_message(current_token)
					raise ContextualSyntaxError("`while` keyword can only be used inside scripts...")
				previous_token = self.tokens[index - 1]
				if previous_token['type'] is not TokenType.ENDOFLINE:
					print_token_error_message(current_token)
					raise ContextualSyntaxError("`while` keyword must be the first word on its line...")
				loop_count += 1
				writer.write_uint8(TokenType.KEYWORD_WHILE.value)
				continue

			elif current_token_type is TokenType.KEYWORD_REPEAT:
				if not parsing_script:
					print_token_error_message(current_token)
					raise ContextualSyntaxError("`repeat` keyword can only be used inside scripts...")
				if loop_count <= 0:
					print_token_error_message(current_token)
					raise ContextualSyntaxError("`repeat` keyword can only be used with while loops...")
				previous_token = self.tokens[index - 1]
				if previous_token['type'] is not TokenType.ENDOFLINE:
					print_token_error_message(current_token)
					raise ContextualSyntaxError("`repeat` keyword must be the first word on its line...")
				loop_count -= 1
				writer.write_uint8(TokenType.KEYWORD_REPEAT.value)
				continue

			elif current_token_type is TokenType.KEYWORD_BREAK:
				if not parsing_script:
					print_token_error_message(current_token)
					raise ContextualSyntaxError("`break` keyword can only be used inside scripts...")
				if loop_count <= 0:
					print_token_error_message(current_token)
					raise ContextualSyntaxError("`break` keyword can only be used inside while loops...")
				previous_token = self.tokens[index - 1]
				if previous_token['type'] is not TokenType.ENDOFLINE:
					print_token_error_message(current_token)
					raise ContextualSyntaxError("`break` keyword must be the first word on its line...")
				writer.write_uint8(TokenType.KEYWORD_BREAK.value)
				continue

			elif current_token_type is TokenType.KEYWORD_RETURN:
				if not parsing_script:
					print_token_error_message(current_token)
					raise ContextualSyntaxError("`return` keyword can only be used inside scripts...")
				previous_token = self.tokens[index - 1]
				if previous_token['type'] is not TokenType.ENDOFLINE:
					print_token_error_message(current_token)
					raise ContextualSyntaxError("`return` keyword must be the first word on its line...")
				writer.write_uint8(TokenType.KEYWORD_RETURN.value)
				continue

			elif current_token_type is TokenType.STARTSTRUCT:
				curly_count += 1
				curly_tracker.append((square_count, curly_count))
				writer.write_uint8(TokenType.STARTSTRUCT.value)
				continue

			elif current_token_type is TokenType.ENDSTRUCT:
				if (curly_count < 1):
					print_token_error_message(current_token)
					raise BracketMismatchError('Curly bracket mismatch!')
				if (curly_tracker[curly_count - 1][0] != square_count):
					print_token_error_message(current_token)
					raise BracketMismatchError('Square bracket mismatch!')
				curly_count -= 1
				curly_tracker.pop(curly_count)
				writer.write_uint8(TokenType.ENDSTRUCT.value)
				continue

			elif current_token_type is TokenType.STARTARRAY:
				square_count += 1
				square_tracker.append((square_count, curly_count))
				writer.write_uint8(TokenType.STARTARRAY.value)
				continue

			elif current_token_type is TokenType.ENDARRAY:
				if (square_count < 1):
					print_token_error_message(current_token)
					raise BracketMismatchError('Square bracket mismatch!')
				if (square_tracker[square_count - 1][1] != curly_count):
					print_token_error_message(current_token)
					raise BracketMismatchError('Curly bracket mismatch!')
				square_count -= 1
				square_tracker.pop(square_count)
				writer.write_uint8(TokenType.ENDARRAY.value)
				continue

			elif current_token_type is TokenType.OPENPARENTH:
				parenth_count += 1
				writer.write_uint8(TokenType.OPENPARENTH.value)
				continue

			elif current_token_type is TokenType.CLOSEPARENTH:
				parenth_count -= 1
				# @todo: handle random stuff here
				writer.write_uint8(TokenType.CLOSEPARENTH.value)
				continue

			elif current_token_type in (TokenType.OPERATOR_SHIFTRIGHT, TokenType.OPERATOR_SHIFTLEFT):
				print_token_error_message(current_token)
				raise NotImplementedError(F"Unsupported operator `{current_token_type}` for `{self.params['game']}`...")
				writer.write_uint8(current_token_type.value)
				continue

			elif current_token_type in (TokenType.GREATERTHANEQUAL, TokenType.LESSTHANEQUAL):
				if self.get_game_type() == GameType.THPG:
					print_token_error_message(current_token)
					raise NotImplementedError(F"Unsupported operator `{current_token_type}` for `{self.params['game']}`...")
				writer.write_uint8(current_token_type.value)
				continue

			# these are not supported... fallback to alternative tokens
			elif current_token_type is TokenType.KEYWORD_AND:
				writer.write_uint8(TokenType.OPERATOR_AND.value)
				continue
			elif current_token_type is TokenType.KEYWORD_OR:
				writer.write_uint8(TokenType.OPERATOR_OR.value)
				continue
			elif current_token_type is TokenType.EQUALS:
				writer.write_uint8(TokenType.ASSIGN.value)
				continue

			elif current_token_type is TokenType.ARGUMENT:
				writer.write_uint8(TokenType.ARGUMENT.value)
				writer.write_uint8(TokenType.NAME.value)
				writer.write_uint32(resolve_checksum_tuple(current_token['value']))
				continue

			elif current_token_type is TokenType.ALLARGS:
				writer.write_uint8(TokenType.ALLARGS.value)
				continue

			elif current_token_type is TokenType.NAME:
				writer.write_uint8(TokenType.NAME.value)
				writer.write_uint32(resolve_checksum_tuple(current_token['value']))
				continue

			elif current_token_type is TokenType.INTEGER:
				writer.write_uint8(TokenType.INTEGER.value)
				writer.write_int32(current_token['value'])
				continue

			elif current_token_type is TokenType.FLOAT:
				writer.write_uint8(TokenType.FLOAT.value)
				writer.write_float(current_token['value'])
				continue

			elif current_token_type is TokenType.PAIR:
				writer.write_uint8(TokenType.PAIR.value)
				writer.write_float(current_token['value'][0])
				writer.write_float(current_token['value'][1])
				continue

			elif current_token_type is TokenType.VECTOR:
				writer.write_uint8(TokenType.VECTOR.value)
				writer.write_float(current_token['value'][0])
				writer.write_float(current_token['value'][1])
				writer.write_float(current_token['value'][2])
				continue

			elif current_token_type in (TokenType.STRING, TokenType.LOCALSTRING):
				writer.write_uint8(current_token_type.value)
				writer.write_uint32(len(current_token['value']))
				writer.write_string(current_token['value'])
				writer.write_uint8(0)
				continue

			elif current_token_type is TokenType.KEYWORD_RANDOMRANGE or current_token_type is TokenType.KEYWORD_RANDOMRANGE2:
				if not parsing_script:
					print_token_error_message(current_token)
					raise InvalidFormatError("`RandomRange` keyword can only be used inside scripts...")
				next_token = self.tokens[index + 1]
				if next_token['type'] is not TokenType.PAIR:
					print_token_error_message(next_token)
					raise InvalidFormatError(F"Expected `{TokenType.PAIR}` token proceeding `{current_token_type}`, but found `{next_token['type']}`...")
				writer.write_uint8(current_token_type.value)
				continue
	
			elif current_token_type in (
				TokenType.KEYWORD_RANDOM,
				TokenType.KEYWORD_RANDOM2,
				TokenType.KEYWORD_RANDOMNOREPEAT,
				TokenType.KEYWORD_RANDOMPERMUTE,
			):
				print_token_error_message(current_token)
				raise NotImplementedError(F"Random keyword `{current_token_type}` is not supported yet...")
				continue

			else:
				# @note: dump all the remaining one-byte tokens here...
				# assuming that they don't require any extra housekeeping
				writer.write_uint8(current_token_type.value)
				continue

		# ---- debugging --------------------------------------------------------------------------
		if debug:
			print('---- tokens --------------------')
			for token in self.tokens:
				print(token)

	# ---------------------------------------------------------------------------------------------
	def to_file(self, filename, params):
		pathname = Path(filename).resolve()
		if not self.stream:
			raise ValueError('The byte stream has no data!')
		print(self.stream.getvalue().hex())
		with open(pathname, 'wb') as out:
			out.write(self.stream.getvalue())
		return True

	# ---------------------------------------------------------------------------------------------
	def to_console(self):
		if not self.stream:
			raise ValueError('The byte stream has no data!')
		print(self.stream.getvalue().hex())
		return True
