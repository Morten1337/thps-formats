import re

import colorama
from colorama import Fore, Style

from pathlib import Path as Path

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
def resolve_checksum_tuple(value):

	# ('Name', 0xA1DC81F9)
	# (None, 0xa1dc81f9)
	# ('Name', None)

	if value[0] is not None:
		checksum = crc32_generate(value[0])
		print('resolving checksum:', str(hex(checksum)))
		return checksum

	if value[1] is not None and isinstance(value[1], int):
		checksum = value[1]
		print('resolving checksum:', str(hex(checksum)))
		return checksum

	raise ValueError('Trying to resolve checksum, but no name or checksum was passed...')


# -------------------------------------------------------------------------------------------------
class InvalidFormatError(Exception):
	pass


# -------------------------------------------------------------------------------------------------
class InvalidTokenError(Exception):
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
	def __init__(self, lines):

		# used for tracking #defined names
		self.defined_names = []
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
			'EQUALS': (TokenType.ASSIGN, None),
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
			'AND': (TokenType.OPERATOR_AND, None),
			'OR': (TokenType.OPERATOR_OR, None),
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
						print(f'Assuming the identifier "{value}" is a `TokenType.NAME`')
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
					print(F'Parsing #goto with name `{value}`')
				elif kind == 'INTERNAL_LABEL':
					kind, value = (TokenType.INTERNAL_LABEL, value.split(':')[0])
					print(F'Parsing label with name `{value}`')

				elif kind == 'INTERNAL_STRCHECKSUM':
					_value = strip_hash_string_stuff(value)
					kind, value = (TokenType.NAME, (_value, None))
					print(F'{Fore.BLUE}Got `INTERNAL_STRCHECKSUM` token with the value "{value[0]}"')
				elif kind == 'INTERNAL_HEXCHECKSUM':
					_value = strip_hash_string_stuff(value)
					kind, value = (TokenType.NAME, (None, int(_value, 0)))
					print(F'{Fore.BLUE}Got `INTERNAL_HEXCHECKSUM` token with the value {value[1]:#010x}')

				elif kind == 'INTERNAL_ARGUMENTSTRCHECKSUM':
					_value = strip_hash_string_stuff(strip_argument_string_stuff(value))
					kind, value = (TokenType.ARGUMENT, (_value, None))
					print(F'{Fore.BLUE}Got `INTERNAL_ARGUMENTSTRCHECKSUM` token with the value "{value[0]}"')
				elif kind == 'INTERNAL_ARGUMENTHEXCHECKSUM':
					_value = strip_hash_string_stuff(strip_argument_string_stuff(value))
					kind, value = (TokenType.ARGUMENT, (None, int(_value, 0)))
					print(F'{Fore.BLUE}Got `INTERNAL_ARGUMENTHEXCHECKSUM` token with the value {value[1]:#010x}')

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

	data = [] # compiled bytes
	debug = [] # debug table
	defines = [] # defined flags
	items = [] # qb items
	tokens = [] # lexer items

	# ---------------------------------------------------------------------------------------------
	def __init__(self):
		pass

	# ---------------------------------------------------------------------------------------------
	@classmethod
	def from_file(cls, filename, params):
		qb = cls() # oaky
		pathname = Path(filename).resolve()
		extension = pathname.suffix.lower().strip('.')

		if not pathname.exists():
			raise FileNotFoundError(f'File does not exist... {pathname}')

		if extension == 'qb':
			raise NotImplementedError('Loading QB scripts is not supported yet...')
		elif extension == 'q':
			try:
				source = LineIterator(pathname)
				qb.compile(source)
			except Exception as exeption:
				print(exeption)
				qb.data = None
		return qb

	# ---------------------------------------------------------------------------------------------
	@classmethod
	def from_string(cls, string, params):
		qb = cls() # oaky
		try:
			source = StringLineIterator(string)
			qb.compile(source)
		except Exception as exeption:
			print(exeption)
			qb.data = None
			return qb

		return qb

	# ---------------------------------------------------------------------------------------------
	def compile(self, source, debug=True):
		print('')
		print('---- tokens --------------------')

		# -----------------------------------------------------------------------------------------
		def get_next_token(tokens):
			try:
				return next(tokens)
			except StopIteration:
				return None

		# -----------------------------------------------------------------------------------------
		token_type_eol = TokenType.ENDOFLINENUMBER if debug else TokenType.ENDOFLINE

		# -----------------------------------------------------------------------------------------
		parsing_script = False
		current_script_name = None
		current_token = None
		iterator = iter(QTokenIterator(source))

		# -----------------------------------------------------------------------------------------
		while (current_token := get_next_token(iterator)) is not None:
			current_token_type = current_token['type']
			current_line = current_token['index']

			if current_token_type is TokenType.ENDOFLINE:
				self.data.append(token_type_eol)
				if debug:
					self.data.append(current_token['value'])

			if current_token_type is TokenType.KEYWORD_SCRIPT:
				if parsing_script:
					raise InvalidFormatError(F"Unexpected `script` keyword while already inside a script at line {current_line}...")

				next_token = get_next_token(iterator)
				if next_token['type'] is not TokenType.NAME:
					print(highlight_error_with_indicator(next_token['source'], next_token['index'], next_token['start'], next_token['end']))
					raise InvalidFormatError(F"Expected script name but found `{next_token['type']}`...")

				parsing_script = True
				current_script_name = next_token['value']
				self.tokens.append(current_token)
				self.tokens.append(next_token)
				self.data.append(TokenType.KEYWORD_SCRIPT)
				self.data.append(TokenType.NAME)
				self.data.append(resolve_checksum_tuple(next_token['value']))
				continue

			elif current_token_type is TokenType.KEYWORD_ENDSCRIPT:
				if not parsing_script:
					raise InvalidFormatError(F"Unexpected `endscript` keyword without matching script at line {current_line}...")
				parsing_script = False
				current_script_name = None
				self.data.append(TokenType.KEYWORD_ENDSCRIPT)

			elif current_token_type is TokenType.NAME:
				self.data.append(TokenType.NAME)
				self.data.append(resolve_checksum_tuple(current_token['value']))

			elif current_token_type is TokenType.PAIR:
				self.data.append(TokenType.PAIR)
				self.data.append(current_token['value'])

			elif current_token_type is TokenType.KEYWORD_RANDOMRANGE or current_token_type is TokenType.KEYWORD_RANDOMRANGE2:
				if not parsing_script:
					raise InvalidFormatError(F"`RandomRange` keyword can only be used inside scripts {current_line}...")

				next_token = get_next_token(iterator)
				if next_token['type'] is not TokenType.PAIR:
					print(highlight_error_with_indicator(next_token['source'], next_token['index'], next_token['start'], next_token['end']))
					raise InvalidFormatError(F"Expected `{TokenType.PAIR}` token proceeding `{current_token_type}`, but found `{next_token['type']}`...")

				self.tokens.append(current_token)
				self.tokens.append(next_token)
				self.data.append(current_token_type)
				self.data.append(TokenType.PAIR)
				self.data.append(next_token['value'])
				continue

			elif current_token_type is TokenType.KEYWORD_RANDOMNOREPEAT:
				print(F"{Fore.BLUE}Got `RandomNoRepeat` keyword and expect the next token to be a `OPENPARENTH`!")

			self.tokens.append(current_token)

		# @todo this should go after the debug table
		#self.tokens.append({
		#	'type': TokenType.ENDOFFILE,
		#	'value': None,
		#	'index': current_line
		#})
		#self.data.append(TokenType.ENDOFFILE)

		# ---- debugging --------------------------------------------------------------------------
		for token in self.tokens:
			print(token)

	# ---------------------------------------------------------------------------------------------
	def to_file(self, filename, params):
		return False
