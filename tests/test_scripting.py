from thps_formats.scripting2 import QB


def test_qb():
	qb = QB.from_file('./tests/data/Example.q', 'THUGPRO')
	assert qb is not None
	assert qb.to_file('./tests/data/Example.qb', 'THUGPRO')
	# @todo: round-trip test
	# @todo: unit test individual
