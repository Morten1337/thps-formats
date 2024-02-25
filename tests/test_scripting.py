from thps_formats.scripting2 import QB, TokenType

defines = ['DEVELOPER', 'TEST']


def test_qb():
	qb = QB.from_file('./tests/data/Example.q', 'THUGPRO', defines)
	assert qb is not None
	assert qb.to_file('./tests/data/Example.qb', 'THUGPRO')
	# @todo: round-trip test
	# @todo: unit test individual


# def test_dumping():
# 	qb = QB.from_string("""
# 	script WaitWhilstChecking
# 		GetStartTime
# 		while
# 			DoNextTrick
# 			if GotParam AndManuals
# 				DoNextManualTrick
# 			endif
# 			Wait 1 GameFrame
# 			GetElapsedTime StartTime = <StartTime>
# 			if (<ElapsedTime> > <Duration>)
# 				break
# 			endif
# 		repeat
# 	endscript
# 	""", 'THUGPRO')
# 	assert qb is not None
# 	assert qb.to_file('./tests/data/Example.qb', 'THUGPRO')

#def test_dumping2():
#	qb = QB.from_string("""
#	script WaitWhilstChecking
#		What = Hello
#		Something = <#"0x00000000">
#		<#"0xf625ce04"> = <#"Hello">
#	endscript
#	""", 'THUGPRO')
#	assert qb is not None
#	assert qb.to_file('./tests/data/Example.qb', 'THUGPRO')

#def test_hash_strings():
#	qb = QB.from_string("""
#	script #"TestHashStrings"
#		#"some value" = #"0xffffffff"
#		#"some thing" = <#"some value">
#		#"some thing" = <#"0xcc489b50">
#	endscript
#	""", 'THUGPRO')
#	assert qb is not None
#	print(qb.data)
#	assert qb.tokens[0]['type'] == TokenType.KEYWORD_SCRIPT
#	assert qb.tokens[1]['type'] == TokenType.NAME
#	assert qb.tokens[2]['type'] == TokenType.NAME
#	assert qb.tokens[3]['type'] == TokenType.ASSIGN
#	assert qb.tokens[4]['type'] == TokenType.NAME
#	assert qb.tokens[5]['type'] == TokenType.NAME
#	assert qb.tokens[6]['type'] == TokenType.ASSIGN
#	assert qb.tokens[7]['type'] == TokenType.ARGUMENT
#	assert qb.tokens[8]['type'] == TokenType.NAME
#	assert qb.tokens[9]['type'] == TokenType.ASSIGN
#	assert qb.tokens[10]['type'] == TokenType.ARGUMENT
#	assert qb.tokens[11]['type'] == TokenType.KEYWORD_ENDSCRIPT

#def test_random_range():
#	qb = QB.from_string("""
#	script HandleKickBoardSound
#		Obj_PlaySound SK6_BoardGrab01 vol = 200 pitch = 80
#		RandomNoRepeat(
#			@Obj_PlaySound BailBodyPunch01_11 pitch = RandomRange(80.0,102.0) vol = RandomRange(50.0,60.0)
#			@Obj_PlaySound BailBodyPunch02_11 pitch = RandomRange(80.0,102.0) vol = RandomRange(50.0,60.0)
#			@Obj_PlaySound BailBodyPunch03_11 pitch = RandomRange(80.0,102.0) vol = RandomRange(50.0,60.0)
#			@Obj_PlaySound BailBodyPunch04_11 pitch = RandomRange(80.0,102.0) vol = RandomRange(50.0,60.0)
#			@Obj_PlaySound BailBodyPunch05_11 pitch = RandomRange(80.0,102.0) vol = RandomRange(50.0,60.0)
#		)
#		Obj_PlaySound SK6_BoardSplit01 pitch = 180 vol = 15
#	endscript
#	""", 'THUGPRO')
#	assert qb is not None
#	assert qb.to_file('./tests/data/Example.qb', 'THUGPRO')

# def test_random_no_repeat():
# 	qb = QB.from_string("""
# 	RandomNoRepeat(
# 		@Obj_PlaySound BailBodyPunch01_11 pitch = (80.0,102.0) vol = (100.0,120.0)
# 		@Obj_PlaySound BailBodyPunch02_11 pitch = (80.0,102.0) vol = (100.0,120.0)
# 		@Obj_PlaySound BailBodyPunch03_11 pitch = (80.0,102.0) vol = (100.0,120.0)
# 		@Obj_PlaySound BailBodyPunch04_11 pitch = (80.0,102.0) vol = (100.0,120.0)
# 		@Obj_PlaySound BailBodyPunch05_11 pitch = (80.0,102.0) vol = (100.0,120.0)
# 	)
# 	""", 'THUGPRO')
# 	assert qb is not None

# 	qb = QB.from_string("""
# 	RandomNoRepeat(
# 		@Obj_PlaySound RU_BellHit01 vol = 50 pitch = 100 emitter = TRG_SFX_SOB_BigBellsRing01
# 		@Obj_PlaySound RU_BellHit01 vol = 80 pitch = 50 emitter = TRG_SFX_SOB_BigBellsRing01
# 		@*5 Obj_PlaySound RU_BellHit01 vol = 30 pitch = 150 emitter = TRG_SFX_SOB_BigBellsRing01
# 		@*2 Obj_PlaySound RU_BellHit01 vol = 50 pitch = 94.41000366 emitter = TRG_SFX_SOB_BigBellsRing01
# 		@*4 Obj_PlaySound RU_BellHit01 vol = 60 pitch = 75 emitter = TRG_SFX_SOB_BigBellsRing01
# 		@*2 Obj_PlaySound RU_BellHit01 vol = 25 pitch = 200 emitter = TRG_SFX_SOB_BigBellsRing01
# 	)
# 	""", 'THUGPRO')
# 	assert qb is not None

# 	qb = QB.from_string('wait RandomNoRepeat(@0.1 @0.14 @0.2 @0.25 @0.28 @0.34) seconds', 'THUGPRO')
# 	assert qb is not None

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
