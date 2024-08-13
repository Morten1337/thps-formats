import os
#import difflib
#import hashlib
from pathlib import Path
from thps_formats.utils.reader import BinaryReader
from thps_formats.utils.diff import find_diff_chunk
from thps_formats.scripting2.qb import QB
from thps_formats.shared.enums import GameVersion


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
		if sourcefile.is_file():
			filecnt += 1
			if index < fileoffset:
				continue
			if index > filelimit:
				break
			if sourcefile.name in skipfiles:
				skipped += 1
				continue
			# output file is `new`, sourcefile is `ref`
			outputfile = outputpath / sourcefile.relative_to(sourcepath)
			difference = find_diff_chunk(outputfile, sourcefile)
			assert difference is False
			thesame += 1
	print('------------------------------------------------------------')
	print(F"Files:   {filecnt}")
	print(F"Equal:   {thesame}")
	print(F"Skipped: {skipped}")
