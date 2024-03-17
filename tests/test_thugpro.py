import os
#import difflib
#import hashlib
from pathlib import Path
from thps_formats.utils.reader import BinaryReader
from thps_formats.scripting2.qb import QB
from thps_formats.shared.enums import GameVersion


# ------------------------------------------------------------------------------
def print_colored_hex_diff(hex_a, hex_b):

	difference = False

	# ANSI escape codes for colors
	RED = '\033[91m'
	GREEN = '\033[92m'
	RESET = '\033[0m'

	# Find the longest hex string for iteration
	max_len = max(len(hex_a), len(hex_b))

	# Pad the shorter string with spaces
	hex_a = hex_a.ljust(max_len)
	hex_b = hex_b.ljust(max_len)

	# Strings to store the color-coded diff
	diff_a = ''
	diff_b = ''

	# Generate diff
	for char_a, char_b in zip(hex_a, hex_b):
		if char_a == char_b:
			diff_a += char_a
			diff_b += char_b
		else:
			difference = True
			diff_a += f'{RED}{char_a}{RESET}'
			diff_b += f'{GREEN}{char_b}{RESET}'

	return (difference, diff_a, diff_b)


# ------------------------------------------------------------------------------
def get_file_chunks(file):
	chunks = []
	with open(file, 'rb') as inp:
		br = BinaryReader(inp)
		br.seek(0, os.SEEK_END)
		end = br.stream.tell()
		br.seek(0, os.SEEK_SET)
		while True:
			remainder = end - br.stream.tell()
			if remainder == 0:
				break
			if remainder >= 16:
				chunkdata = br.read_bytes(16)
			else:
				chunkdata = br.read_bytes(remainder)
			chunks.append(chunkdata)
	return chunks


# ------------------------------------------------------------------------------
def find_diff_chunk(new, ref):
	print(F"[calculating diff for '{new.name}']")
	difference = False
	fileoffset = 0
	chunksnew = get_file_chunks(new)
	chunksref = get_file_chunks(ref)
	for a, b in zip(chunksnew, chunksref):
		difference, diffnew, diffref = print_colored_hex_diff(a.hex(), b.hex())
		if difference is True:
			print(F"{new.name} {fileoffset:#010x} | {diffnew} # new")
			print(F"{ref.name} {fileoffset:#010x} | {diffref} # reference")
			break
		fileoffset += 16
	return difference


# ------------------------------------------------------------------------------
params = {
	'debug': False,
	'game': GameVersion.THUGPRO_WIN,
	'root': Path('./tests/data/thugpro').resolve()
}

# ------------------------------------------------------------------------------
defines = [
	'DEVELOPER', 'DEVELOPER_FAST_GETUP',
	'DEVELOPER_NERF_EXPLOITS', 'HALLOWEEN_SPECIAL',
	'GIVE_ME_EXTRA_DROPDOWN_CONTROLS', 'GIVE_ME_HIGH_OLLIE',
	'GIVE_ME_CUSTOM_LEVEL_RELOAD', 'GIVE_ME_BALANCE_INDICATORS',
	'GIVE_ME_THPS3_THEME', 'UNLOCKED_CLAYTONS_SHIP',
	'USE_MENU_FOR_NET_PANEL_MESSAGES',
	'DEFRAG_ANIM_CACHE_ON_LEVEL_CLEANUP', 
]

# ------------------------------------------------------------------------------
sourcepath = Path('./tests/data/thugpro/source/code/qb').resolve()
outputpath = Path('./tests/data/thugpro/output/data/qb').resolve()
fileoffset = 0
filelimit = 300

skipfiles = [
	# include directives omits newline tokens in qconsole
	'tod_manager.qb', 'thugpro_levelselect.qb',
	# text encoding issues in qconsole with char `œ` `0x9C`
	'keyboard.qb', 'net.qb',
	# qconsole parses `!` as a name `if ! InVertAir`
	'ksk_tricks.qb',
	# qcompy does not handle #raw bytes yet 
	'thug_pro_dev_menu.qb',
]


# ------------------------------------------------------------------------------
def file_ends_with_empty_line(filepath):
	with open(filepath, 'rb') as file:
		# Seek to the last byte of the file
		file.seek(-1, 2)  # 2 means relative to the file's end
		last_byte = file.read(1)
		# Check if the last byte is a newline character
		if last_byte == b'\n':
			return True
		# For Windows-style endings, check the last two bytes for '\r\n'
		if last_byte == b'\r':
			file.seek(-2, 2)  # Move two bytes before the end
			second_last_byte = file.read(1)
			if second_last_byte == b'\n':
				return True
	return False


## ------------------------------------------------------------------------------
#def test_aaaaa():
#	for sourcefile in sourcepath.rglob('*.q'):
#		if sourcefile.is_file():
#			print(F"Checking for trailing whitespace in file '{sourcefile}'")
#			whitespace = file_ends_with_empty_line(sourcefile)
#			assert whitespace is True


# ------------------------------------------------------------------------------
def test_compile():
	for index, sourcefile in enumerate(sourcepath.rglob('*.q')):
		if index < fileoffset:
			continue
		if index > filelimit:
			break 
		if sourcefile.is_file():
			outputfile = outputpath / sourcefile.relative_to(sourcepath).with_suffix('.qb')
			outputfile.parent.mkdir(exist_ok=True, parents=True)
			print(F"[{index}] Compiling file '{sourcefile}'")
			qb = QB.from_file(sourcefile, params, defines)
			assert qb is not None
			assert qb.to_file(outputfile, params)


# ------------------------------------------------------------------------------
def test_difference():
	skipped = 0
	thesame = 0
	filecnt = 0
	for index, sourcefile in enumerate(sourcepath.rglob('*.qb')):
		if index < fileoffset:
			continue
		if index > filelimit:
			break
		if sourcefile.name in skipfiles:
			skipped += 1
			continue
		if sourcefile.is_file():
			filecnt += 1
			# output file is `new`, sourcefile is `ref`
			outputfile = outputpath / sourcefile.relative_to(sourcepath)
			difference = find_diff_chunk(outputfile, sourcefile)
			assert difference is False
			thesame += 1
	print('------------------------------------------------------------')
	print(F"Files:   {filecnt}")
	print(F"Equal:   {thesame}")
	print(F"Skipped: {skipped}")
