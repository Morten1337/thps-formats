import re

from enum import Enum, IntEnum
from pathlib import Path as Path

# --- notes ---------------------------------------------------------------------------------------
# so far we handle the following
# - block comments `/* hello */`
# - inline comments `; //`
# - vectors `(0,1) (0.1,0.2,0.3)`
# - parentheses `(value)
# - arguments `<value>`
# - all args `<...>`
# - less than, greater than, shift etc `> < >= <= >> <<` 
# - equals and assignment `== =`
# - arrays `[]`
# - structures `{}`
# - strings - including escapes


# --- todo ----------------------------------------------------------------------------------------
# - EOL and EOF tokens 
# - ✔ strings
# - ✔ comments
# - ✔ structures
# - ✔ arrays
# - ✔ equals, sameas
# - ✔ operators
# - ✔ close parenth
# - ✔ greater than
# - ✔ open parenth, vector, pair
# - ✔ lessthan, argument
# - ✔ float
# - ✔ integers
# - ✔ divide
# - ✔ dot
# - ✔ comma
# - ✔ at @
# - ✔ colon
# - ✔ and && 
# - ✔ or ||
# - kewords
# - words
# - hash tag

# -------------------------------------------------------------------------------------------------
class InvalidFormatError(Exception):
	pass


# -------------------------------------------------------------------------------------------------
class InvalidTokenError(Exception):
	pass


# -------------------------------------------------------------------------------------------------
class TokenType(Enum):
	ENDOFFILE = 0x00
	ENDOFLINE = 0x01
	NAME = 0x16
	INTEGER = 0x17
	STRING = 0x1B


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

	in_block_comment = False

	@classmethod
	def is_token_char(cls, value):
		return value in '{}[]=.,-+/*()<>#"\'@|&^:;\\'

	def __init__(self, lines):
		self.lines = lines
		self.line_count = 0
		self.token_specs = [
			('BLOCK_COMMENT_OPEN', r'\/\*'), # Open block comment
			('BLOCK_COMMENT_CLOSE', r'\*\/'), # Close block comment
			('INLINE_COMMENT', r'(\/\/|;)[^\n]*'), # Inline comments starting with `//` or `;`

			('OPEN_STRUCT', r'\{'), # Open struct
			('CLOSE_STRUCT', r'\}'), # Close struct
			('OPEN_ARRAY', r'\['), # Open array
			('CLOSE_ARRAY', r'\]'), # Close array

			('EQUALS', r'=='), # Equality comparison
			('ASSIGN', r'='), # Assignment

			('VECTOR_PAIR', r'\(([^\(\)]*,[^\(\)]*,?[^\(\)]*)\)'), # Matches simple vectors/pairs
			('OPEN_PAREN', r'\('), # Opening parenthesis
			('CLOSE_PAREN', r'\)'), # Closing parenthesis

			('ALLARGS', r'<\.\.\.>'),
			('ARGUMENT', r'<[a-zA-Z_][a-zA-Z0-9_]*>'),

			('OR', r'\|\|'), # Logical OR
			('AND', r'&&'), # Logical AND
			('COLON', r'::'),

			('SHIFTRIGHT', r'>>'),
			('SHIFTLEFT', r'<<'),
			('GREATERTHANEQUAL', r'>='),
			('LESSTHANEQUAL', r'<='),
			('GREATERTHAN', r'>'),
			('LESSTHAN', r'<'),

			('STRING', r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\''),  # Quoted strings with escaped quotes

			('FLOAT', r'-?\b\d+\.\d*|-?\.\d+\b'), # Matches floats with leading digits, or starting with a dot
			('INTEGER', r'-?\b\d+\b'), # Matches integers, possibly negative

			# Patterns for arithmetic operators, ensuring they don't conflict with negative numbers or comments
			('PLUS', r'\+'),
			('MINUS', r'(?<!\d)-(?!\d)'),  # Negative lookahead and lookbehind to avoid matching negative numbers
			('MULTIPLY', r'\*'),
			('DIVIDE', r'\/'),
			('DOT', r'\.(?!\d)'),
			('AT', r'@'),
			('COMMA', r','),

			#('PUNCTUATION', r'[,.:;()\[\]{}]'),  # Punctuation
			('IDENTIFIER', r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'),  # Identifiers
			('SKIP', r'[ \t]+'),  # Skip spaces and tabs
			('NEWLINE', r'\n'),  # Newlines
			('MISMATCH', r'.'),  # Any other character
		]
		self.tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in self.token_specs)

	# -------------------------------------------------------------------------------------------------
	def extract_numbers_to_tuple(self, value):
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

	def tokenize_line(self, line):
		for mo in re.finditer(self.tok_regex, line):
			kind = mo.lastgroup
			value = mo.group()

			if self.in_block_comment:
				if kind == 'BLOCK_COMMENT_CLOSE':
					self.in_block_comment = False
				continue # Ignore all tokens until block comment is closed
			elif kind == 'BLOCK_COMMENT_OPEN':
				self.in_block_comment = True
				continue

			if kind == 'VECTOR_PAIR':
				result, count = self.extract_numbers_to_tuple(value)
				if count == 2:
					kind, value = ('PAIR', result)
				elif count == 3:
					kind, value = ('VECTOR', result)
				else:
					# @todo: print line number and code snippet
					raise InvalidFormatError(f'Unexpected number of elements found when parsing vector: {count} detected... {value}')

			elif kind == 'FLOAT':
				value = float(value)

			elif kind == 'INTEGER':
				value = int(value)

			elif kind == 'IDENTIFIER':
				if value.upper() in ('WHILE', 'BEGIN', 'REPEAT', 'BREAK', 'SCRIPT', 'ENDSCRIPT', 'IF', 'DOIF', 'ELSE', 'DOELSE', 'ELSEIF', 'DOELSEIF', 'ENDIF', 'RETURN', 'RANDOMRANGE', 'RANDOMRANGE2', 'RANDOM', 'RANDOM2', 'RANDOMNOREPEAT', 'RANDOMPERMUTE', 'RANDOMSHUFFLE', 'NOT', 'AND', 'OR', 'XOR', 'SWITCH', 'ENDSWITCH', 'CASE', 'DEFAULT', 'NAN'):
					print('-- KEYWORD:', value)
				else:
					print('-- IDENTIFIER:', value)

			elif kind == 'MISMATCH':
				print('-- MISMATCH:', value)

			elif kind == 'ARGUMENT':
				if '#' in value:
					raise NotImplementedError('Hash names or checksum names in arguments is not supported yet...')

			elif kind in ('INLINE_COMMENT', 'SKIP', 'MISMATCH', 'NEWLINE'):
				continue # Skip spaces, newlines, and mismatches
			yield kind, value

	def __iter__(self):
		for index, line in self.lines:
			self.line_count = index

			# skipping whitespace...
			if not line.strip():
				continue

			for kind, value in self.tokenize_line(line.strip()):
				token = {
					'type': kind,
					'value': value,
					'line_index': index,
				}
				yield token

			# @note: This method validates token types on a syntactical (micro) level only,
			# such as checking if the token type is recognized and can be parsed successfully.
			# Macro-level validations, including tracking of open braces and other structural 
			# considerations, should be performed by the calling function.

			# @todo: properly handle tokens...
			#for word in line.strip().split():
			#	token = {
			#		'type': TokenType.NAME,
			#		'value': word,
			#		'line_index': index,
			#	}
			#	yield token


# -------------------------------------------------------------------------------------------------
class QB:

	data = [] # compiled bytes
	debug = [] # debug table
	defines = [] # defined flags
	items = [] # qb items

	def __init__(self):
		pass

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
		return qb

	def compile(self, source):
		#items = []
		try:
			iterator = QTokenIterator(source)
			print('')
			print('---- tokens --------------------')
			for token in iterator:
				pass
				#print(token)
		except StopIteration:
			print("End of file reached")
		#for token in items:
		#	print(token)

	def to_file(self, filename, params):
		return False
