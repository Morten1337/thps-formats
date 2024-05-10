from thps_formats.scripting2.qb import QB
from thps_formats.shared.enums import GameVersion

defines = ['DEVELOPER', 'TEST']
params = {
	'debug': False,
	'game': GameVersion.THUGPRO_WIN
}


def test_nodearray():
	qb = QB.from_file('./tests/data/ba.q', params, defines)
	assert qb is not None
	assert qb.to_json('./tests/data/ba.json')


def test_shp_scripts():
	qb = QB.from_file('./tests/data/shp_scripts.q', params, defines)
	assert qb is not None
	assert qb.to_json('./tests/data/shp_scripts.json')
