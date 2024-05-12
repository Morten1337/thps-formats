from enum import Enum


# -------------------------------------------------------------------------------------------------
class ComponentType(Enum):
	NONE = 'NONE'
	INTEGER = 'INTEGER'
	FLOAT = 'FLOAT'
	STRING = 'STRING'
	PAIR = 'PAIR'
	VECTOR = 'VECTOR'
	SCRIPT = 'SCRIPT'
	NAME = 'NAME'


# -------------------------------------------------------------------------------------------------
class TokenType(Enum):

	# Misc
	ENDOFFILE = 0x00
	ENDOFLINE = 0x01
	ENDOFLINENUMBER = 0x02
	STARTSTRUCT = 0x03
	ENDSTRUCT = 0x04
	STARTARRAY = 0x05
	ENDARRAY = 0x06

	ASSIGN = 0x07
	DOT = 0x08
	COMMA = 0x09
	MINUS = 0x0A
	ADD = 0x0B
	DIVIDE = 0x0C
	MULTIPLY = 0x0D

	OPENPARENTH = 0x0E
	CLOSEPARENTH = 0x0F

	# This is ignored by the interpreter.
	# Allows inclusion of source level debugging info, eg line number.
	DEBUGINFO = 0x10

	# Comparison
	EQUALS = 0x11 # SameAs
	LESSTHAN = 0x12
	LESSTHANEQUAL = 0x13 # doesn't work in THUG1+; works in THPG
	GREATERTHAN = 0x14
	GREATERTHANEQUAL = 0x15 # doesn't work in THUG1+; works in THPG

	# Types
	NAME = 0x16
	INTEGER = 0x17
	HEXINTEGER = 0x18 # Only used internally by the compiler
	ENUM = 0x19
	FLOAT = 0x1A
	STRING = 0x1B
	LOCALSTRING = 0x1C
	ARRAY = 0x1D # eh
	VECTOR = 0x1E
	PAIR = 0x1F

	# Keywords
	KEYWORD_WHILE = 0x20
	KEYWORD_REPEAT = 0x21
	KEYWORD_BREAK = 0x22
	KEYWORD_SCRIPT = 0x23
	KEYWORD_ENDSCRIPT = 0x24
	KEYWORD_IF = 0x25
	KEYWORD_ELSE = 0x26
	KEYWORD_ELSEIF = 0x27
	KEYWORD_ENDIF = 0x28
	KEYWORD_RETURN = 0x29
	KEYWORD_UNDEFINED = 0x2A

	# For debugging
	CHECKSUM_NAME = 0x2B

	# Token for the <...> symbol
	ALLARGS = 0x2C
	# Token that preceds a name when the name is enclosed in < > in the source.
	ARGUMENT = 0x2D

	# A relative jump. Used to speed up if-else-endif and break statements, and
	# used to jump to the end of lists of items in the random operator.
	JUMP = 0x2E

	# Precedes a list of items that are to be randomly chosen from
	KEYWORD_RANDOM = 0x2F
	# Precedes two integers enclosed in parentheses
	KEYWORD_RANDOMRANGE = 0x30

	# Only used internally by the compiler
	KEYWORD_AT = 0x31

	# Logical operators
	OPERATOR_OR = 0x32
	OPERATOR_AND = 0x33
	OPERATOR_XOR = 0x34

	# Shift operators
	OPERATOR_SHIFTLEFT = 0x35
	OPERATOR_SHIFTRIGHT = 0x36

	# These versions use the Rnd2 function, for use in certain things so as not to mess up
	# the determinism of the regular Rnd function in replays.
	KEYWORD_RANDOM2 = 0x37
	KEYWORD_RANDOMRANGE2 = 0x38

	KEYWORD_NOT = 0x39
	KEYWORD_AND = 0x3A
	KEYWORD_OR = 0x3B
	KEYWORD_SWITCH = 0x3C
	KEYWORD_ENDSWITCH = 0x3D
	KEYWORD_CASE = 0x3E
	KEYWORD_DEFAULT = 0x3F
	KEYWORD_RANDOMNOREPEAT = 0x40
	KEYWORD_RANDOMPERMUTE = 0x41

	# hehe
	COLON = 0x42

	# THUG2 additional tokens
	KEYWORD_IF2 = 0x47
	KEYWORD_ELSE2 = 0x48
	KEYWORD_SHORTJUMP = 0x49

	# Compiler
	# These output as Jump tokens 0x2E but are used outside of randoms so we need to handle them differently in code.
	INTERNAL_DEFINE = 0x52
	INTERNAL_IFDEF = 0x53
	INTERNAL_ELSEDEF = 0x54
	INTERNAL_ENDIFDEF = 0x55
	INTERNAL_IFNDEF = 0x56
	INTERNAL_LABEL = 0x57
	INTERNAL_GOTO = 0x58
	INTERNAL_INCLUDE = 0x5F
	INTERNAL_RAW = 0x60

	# ---------------------------------------------------------------------------------------------
	def __int__(self):
		return self.value
