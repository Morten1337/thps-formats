from pathlib import Path
from thps_formats.scripting2.qb import QB, QArray
from thps_formats.shared.enums import GameVersion

# -------------------------------------------------------------------------------------------------
defines = ['__IGNORE_IFDEF_CONDITIONS__']
params = {'game': GameVersion.THUGPRO_WIN}


# -------------------------------------------------------------------------------------------------
def write_line(out, text, indent=0):
	indentation = '\t' * indent
	out.write(F"{indentation}{text}\n")


# -------------------------------------------------------------------------------------------------
def test_levelpreview():

	# ---------------------------------------------------------------------------------------------
	levels = []
	ouputfile = Path('./tests/data/thugpro/source/generated/levelselect/level_preview_texture_lookup_new.q')
	directory = Path('./tests/data/thugpro/source/generated/levelselect/')

	# --- parse level select lists ----------------------------------------------------------------
	for f in directory.glob('levelselect_*.q'):
		print(f)
		qb = QB.from_file(f, params, defines).to_struct(scope=QArray())
		for level in qb:
			levels.append((level.get_value('text'), level.get_value('level_thumb')))
			print(levels[-1])

	# --- generate sprite lookup script -----------------------------------------------------------
	with open(ouputfile, 'w') as out:
		write_line(out, 'script get_level_thumb_texture_from_level_name_checksum')
		write_line(out, 	'switch <level_name_checksum>', indent=1)
		for level in levels:
			write_line(out, 	F'case #"{level[0]}"', indent=2)
			write_line(out, 		F'level_thumb = {level[1]}', indent=3)
		write_line(out, 		'default', indent=2)
		write_line(out, 			'level_thumb = flare1', indent=3)
		write_line(out, 	'endswitch', indent=1)
		write_line(out, 	'return level_thumb = <level_thumb>', indent=1)
		write_line(out, 'endscript')
