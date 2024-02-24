from thps_formats.scripting2 import QB


def test_qb():
	qb = QB.from_file('./tests/data/Example.q', 'THUGPRO')
	assert qb is not None
	#assert qb.to_file('./tests/data/Example.qb', 'THUGPRO')
	# @todo: round-trip test
	# @todo: unit test individual

#def test_qb2():
#	source = [
#		'	GlobalName = animload_THPS6_human',
#		'	GlobalString = "Water: Main Level"',
#		'	GlobalVec3 = (3.14159298,-0.75049102,3.14159298)',
#		'	GlobalVec2 = (0.00000000,1.00000000)',
#		'	GlobalSimpleArray = [MultiPlayer Horse]',
#		'	GlobalInteger = 1234 // inline comment',
#		'	GlobalFloat = 3.14159298',
#	]	
#	qb = QB.from_string(source, 'THUGPRO')
#	assert qb is not None
#	assert qb.tokens[0] == 'IDENTIFIER'
#	assert qb.tokens[1] == 'ASSIGN'
#	assert qb.tokens[2] == 'IDENTIFIER'
#
#	assert qb.tokens[3] == 'IDENTIFIER'
#	assert qb.tokens[4] == 'ASSIGN'
#	assert qb.tokens[5] == 'STRING'
#
#	assert qb.tokens[6] == 'IDENTIFIER'
#	assert qb.tokens[7] == 'ASSIGN'
#	assert qb.tokens[8] == 'VECTOR'
#	print(qb.tokens)
