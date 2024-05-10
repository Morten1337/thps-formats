from thps_formats.scripting2.qb import QB
from thps_formats.shared.enums import GameVersion

defines = ['DEVELOPER', 'TEST']
params = {
	'debug': False,
	'game': GameVersion.THUGPRO_WIN
}


# def test_nodearray():
# 	qb = QB.from_file('./tests/data/ba.q', params, defines)
# 	assert qb is not None
# 	assert qb.to_json('./tests/data/ba.json')

# def test_cas_skater_shared():
# 	qb = QB.from_file('./tests/data/thugpro/source/code/qb/game/cas_skater_shared.q', params, defines)
# 	assert qb is not None
# 	assert qb.to_json('./tests/data/cas_skater_shared.json')

# def test_shp_scripts():
# 	qb = QB.from_file('./tests/data/shp_scripts.q', params, defines)
# 	assert qb is not None
# 	assert qb.to_json('./tests/data/shp_scripts.json')

# def test_hex():
# 	qb = QB.from_string("""
# 	Structure = {
# 		Name = #"0xf625ce04"
# 		Type = #"hello world"
# 		#"0x278081f3"
# 	}
# 	Test = {
# 		foo = "bar"
# 	}
# 	#"0x278081f3" = {
# 		foo = "bar"
# 	}
# 	""", params)
# 	assert qb is not None
# 	test = qb.to_struct(resolve=True)
# 	print(test['Structure'])
# 	print(test['Structure'].get('foo'))
# 	assert qb.to_json('./tests/data/structure.json')

# def test_nodearray2():
# 	qb = QB.from_file('./tests/data/ba.q', params, defines)
# 	assert qb is not None
# 	baq = qb.to_struct(resolve=True)
# 	nodearray = baq['BA_NodeArray']
# 	for node in nodearray:
# 		# print(node.keys())
# 		if 'DAY_ON' in node:
# 			print(node.get('day_on'))
# 			print(node.get('Pos'))
# 			print(F"-- Found node `{node['Name']}` with flag `Day_on` ")

node_name_patterns_morning = [
	'MORNINGON_',
	'DAYOFF_',
	'AFTERNOONOFF_',
	'EVENINGOFF_',
	'NIGHTOFF_',
	'TRG_SFX_SOB_MORNING_',
	'TRG_SFX_TRIGBOX_MORNING_',
	'TRG_MORNING_LEVELLIGHT',
]

node_name_patterns_afternoon = [
	'DAYON_',
	'AFTERNOONON_',
	'MORNINGOFF_',
	'EVENINGOFF_',
	'NIGHTOFF_',
	'TRG_SFX_SOB_DAY_',
	'TRG_SFX_TRIGBOX_DAY_',
	'TRG_DAY_LEVELLIGHT',
	'TRG_AFTERNOON_LEVELLIGHT',
]

node_name_patterns_evening = [
	'EVENINGON_',
	'MORNINGOFF_',
	'DAYOFF_',
	'AFTERNOONOFF_',
	'NIGHTOFF_',
	'TRG_SFX_SOB_EVENING_',
	'TRG_SFX_TRIGBOX_EVENING_',
	'TRG_EVENING_LEVELLIGHT',
]

node_name_patterns_night = [
	'NIGHTON_',
	'MORNINGOFF_',
	'DAYOFF_',
	'AFTERNOONOFF_',
	'EVENINGOFF_',
	'TRG_SFX_SOB_NIGHT_',
	'TRG_SFX_TRIGBOX_NIGHT_',
	'TRG_LEVELLIGHT',
	'TRG_NIGHT_LEVELLIGHT',
]


def _handle_tod_on_flag(node, flagname):
	if flagname in node:
		# None is also valid, because in thug1 this can be a flag...
		return str(node.get(flagname)).upper() in ['NONE', '1', 'TRUE']


def _handle_default_object(node):
	if 'CreatedAtStart' in node:
		return True
	elif 'CreatedFromVariable' in node:
		if int(node.root.get(str(node.get('CreatedFromVariable')), 0)) > 0:
			return True
	elif int(node.get('Brightness', 0)) > 0:
		return True
	else:
		return False


def test_todscripts():

	scenename = 'ba'
	qb = QB.from_file(F"./tests/data/{scenename}.q", params, defines)
	assert qb is not None
	level = qb.to_struct(resolve=True)

	nodearray = level[F"{scenename}_NodeArray"]

	all_objects = set()
	default_objects = set()
	morning_objects = set()
	afternoon_objects = set()
	evening_objects = set()
	night_objects = set()

	for node in nodearray:

		if 'Name' not in node:
			raise ValueError('Node has no name!', node)
		all_objects.add(node.get('Name')) # @debug

		node_name = str(node.get('Name'))
		created_from_tod = str(node.get('CreatedFromTOD', ''))

		if 'IgnoreTOD' in node:
			print(F"Skipping node with `IgnoreTOD` flag `{node_name}`!")
			continue

		# this checks for nodes that have a matching pattern in the name...
		if any(p in node_name.upper() for p in node_name_patterns_morning):
			morning_objects.add(node)
		elif any(p in node_name.upper() for p in node_name_patterns_afternoon):
			afternoon_objects.add(node)
		elif any(p in node_name.upper() for p in node_name_patterns_evening):
			evening_objects.add(node)
		elif any(p in node_name.upper() for p in node_name_patterns_night):
			night_objects.add(node)

		# this checks for nodes that have a `CreatedFromTOD` variable...
		elif any(p in created_from_tod.upper() for p in ['MORNINGON', 'DAYOFF', 'AFTERNOONOFF', 'NIGHTOFF']):
			morning_objects.add(node)
		elif any(p in created_from_tod.upper() for p in ['DAYON', 'AFTERNOONON', 'MORNINGOFF', 'AFTERNOONOFF', 'NIGHTOFF']):
			afternoon_objects.add(node)
		elif any(p in created_from_tod.upper() for p in ['EVENINGON', 'MORNINGOFF', 'DAYOFF', 'AFTERNOONOFF', 'NIGHTOFF']):
			evening_objects.add(node)
		elif any(p in created_from_tod.upper() for p in ['NIGHTON', 'MORNINGOFF', 'DAYOFF', 'AFTERNOONOFF', 'EVENINGOFF']):
			night_objects.add(node)

		# this checks for nodes that have the tod state `*_On` flag...
		elif _handle_tod_on_flag(node, 'Morning_On'):
			morning_objects.add(node)
		elif _handle_tod_on_flag(node, 'Day_On'):
			afternoon_objects.add(node)
		elif _handle_tod_on_flag(node, 'Evening_On'):
			evening_objects.add(node)
		elif _handle_tod_on_flag(node, 'Night_On'):
			night_objects.add(node)

	# this checks for nodes that are time of day specific, but that are created by default for some reason!
	# we need this so that we can restore a "true" default day state, where these objects are not created...
	for node in morning_objects:
		if _handle_default_object(node):
			default_objects.add(node)
	for node in evening_objects:
		if _handle_default_object(node):
			default_objects.add(node)
	for node in night_objects:
		if _handle_default_object(node):
			default_objects.add(node)

	print(F"--- Parsed {len(all_objects)} nodes!")
	print(F"Found {len(morning_objects)} morning nodes!")
	print(F"Found {len(afternoon_objects)} afternoon nodes!")
	print(F"Found {len(evening_objects)} evening nodes!")
	print(F"Found {len(night_objects)} night nodes!")
