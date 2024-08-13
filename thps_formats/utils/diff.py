import os
from thps_formats.utils.reader import BinaryReader


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
			print(F"{fileoffset:#010x} | {diffnew} # {new.name}")
			print(F"{fileoffset:#010x} | {diffref} # {ref.name}")
			break
		fileoffset += 16
	return difference
