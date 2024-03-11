import pytest
from pathlib import Path

from thps_formats.scripting2.qb import QB
from thps_formats.scripting2.enums import TokenType
from thps_formats.shared.enums import (
	GameVersion,
	GameType,
	PlatformType
)

defines = ['DEVELOPER', 'TEST']
params = {
	'debug': False,
	'game': GameVersion.THUGPRO_WIN
}


def test_thugpro():
	sourcepath = Path('d:/repos/thugpro/source/code/qb').resolve()
	outputpath = Path('./tests/data/qb').resolve()
	for sourcefile in sourcepath.rglob('*.q'):
		if sourcefile.is_file():
			outputfile = outputpath / sourcefile.relative_to(sourcepath).with_suffix('.qb')
			outputfile.parent.mkdir(exist_ok=True, parents=True)
			qb = QB.from_file(sourcefile, params, defines)
			assert qb is not None
			assert qb.to_file(outputfile, params)

#def test_qb():
#	qb = QB.from_file('./tests/data/Example.q', params, defines)
#	assert qb is not None
#	assert qb.to_file('./tests/data/Example.qb', params)

# def test_switch():
# 	qb = QB.from_string("""
# 	script SwitchTest
# 		switch <next_tod>
# 			case morning
# 				next_tod_string = "Morning"
# 			case afternoon
# 				next_tod_string = "Day"
# 			case evening
# 				next_tod_string = "Evening"
# 			case night
# 				next_tod_string = "Night"
# 			default
# 				next_tod_string = "Day"
# 		endswitch
# 		switch (tod_current_state)
# 			case morning
# 				current_tod_string = "Morning"
# 			case afternoon
# 				current_tod_string = "Day"
# 			case evening
# 				current_tod_string = "Evening"
# 			case night
# 				current_tod_string = "Night"
# 			default
# 				current_tod_string = "Day"
# 		endswitch
# 		Change tod_current_state = <next_tod>
# 		return current_tod_string = <current_tod_string> next_tod_string = <next_tod_string>
# 	endscript
# 	""", params)
# 	assert qb is not None
# 	assert qb.to_console()


#def test_random2():
#	qb = QB.from_file('./tests/data/random.q', params, defines)
#	assert qb is not None
#	assert qb.to_file('./tests/data/random2.qb', params)


#def test_random3():
#	qb = QB.from_file('./tests/data/randomweights.q', params, defines)
#	assert qb is not None
#	assert qb.to_file('./tests/data/randomweights2.qb', params)


#def test_random():
#	qb = QB.from_string("""
#	script PlayWalkStandAnim
#		while
#			PlayWalkAnim BlendPeriod = 0.1 Anim = Random(@*3 WStand @RandomNoRepeat(@WStandIdle1 @WStandIdle2 @WStandIdle3 @WStandIdle4 @WStandIdle5 @WStandIdle6))
#			WaitAnimWalking
#		repeat
#	endscript
#	script FL_SFX_GarageWarp01
#		RandomNoRepeat(
#			@Obj_PlayStream FL_ParkingGarageHorn01 emitter = TRG_SFX_SOB_GarageWarp01
#			@Obj_PlayStream FL_ParkingGarageHorn02 emitter = TRG_SFX_SOB_GarageWarp01
#			@Obj_PlayStream FL_ParkingGarageHorn03 emitter = TRG_SFX_SOB_GarageWarp01
#			@Obj_PlayStream FL_ParkingGarageHorn04 emitter = TRG_SFX_SOB_GarageWarp01
#		)
#	endscript
#	""", params)
#	assert qb is not None
#	assert qb.to_file('./tests/data/test_random.qb', params)


# def test_ifs():
# 	qb = QB.from_string("""
# 	script IfTests
# 		if (<Something> == 1)
# 			<Something> = 0
# 		endif

# 		if NOT (<Something> == 1)
# 			<Something> = 1
# 		endif

# 		if IsTrue Whatever
# 			Change Whatever = 0
# 		endif

# 		if (Whatever)
# 			print "hello"
# 		else
# 			if (<Something>)
# 				print "hmm"
# 			else
# 				print "okay"
# 			endif
# 		endif

# 	endscript
# 	""", params)
# 	assert qb is not None
# 	assert qb.to_console()
# 	assert qb.to_file('./tests/data/test.qb', params)

# def test_scripts():
# 	with pytest.raises(Exception):
# 		QB.from_string("""
# 		script "garbage"
# 			// should fail because string name
# 		endscript
# 		""")


# def test_scripts2():
# 	with pytest.raises(Exception):
# 		QB.from_string("""
# 		script ReturnTest
# 			// fails because return needs to be first on its line
# 			Something return { Result = 1 }
# 		endscript
# 		""")


# def test_scripts3():
# 	with pytest.raises(Exception):
# 		QB.from_string("""
# 			// fails because return needs to be in a script
# 			return { Result = 1 }
# 		""")


# def test_scripts4():
# 	with pytest.raises(Exception):
# 		QB.from_string("""
# 			// fails because while needs to be in a script
# 			while
# 		""")


# def test_scripts5():
# 	with pytest.raises(Exception):
# 		QB.from_string("""
# 			// fails because repeat needs to be in a script
# 			repeat
# 		""")


# def test_scripts6():
# 	with pytest.raises(Exception):
# 		QB.from_string("""
# 			// fails because break needs to be in a script
# 			break
# 		""")


# def test_script_loops():
# 	with pytest.raises(Exception):
# 		QB.from_string("""
# 			script LoopTest
# 				while
# 					printf "foo"
# 				repeat 5
# 				break
# 			endscript
# 		""")

# 		QB.from_string("""
# 			script LoopTest
# 			endscript
# 		""")


# def test_strings():
# 	qb = QB.from_string("""
# 	{
# 		desc_id = Fly
# 		frontend_desc = 'Fly'
# 		mesh = "models/skater_male/specs_fly.skin"
# 	}
# 	""", params)
# 	assert qb is not None
# 	assert qb.to_console()
# 	assert qb.to_file('./tests/data/test.qb', params)


# def test_brackets():
# 	qb = QB.from_string("""
# 	glasses = [
# 		{
# 			desc_id = None
# 			frontend_desc = 'None'
# 			no_color
# 		}
# 		{
# 			desc_id = #"Burnquist Glasses"
# 			frontend_desc = 'Burnquist Style'
# 			mesh = "models/skater_male/specs_burnquist.skin"
# 		}
# 		{
# 			desc_id = SkiGoggles
# 			frontend_desc = 'Ski Goggles'
# 			mesh = "models/skater_male/specs_skigoggles.skin"
# 		}
# 		{
# 			desc_id = Specs_Nigel_Costume
# 			frontend_desc = 'Nigel Mask'
# 			mesh = "models/skater_male/Specs_Nigel_Costume.skin"
# 		}
# 	]
# 	""", params)
# 	assert qb is not None
# 	assert qb.to_console()

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
# 	""", params)
# 	assert qb is not None
# 	assert qb.to_file('./tests/data/Example.qb', params)

#def test_dumping2():
#	qb = QB.from_string("""
#	script WaitWhilstChecking
#		What = Hello
#		Something = <#"0x00000000">
#		<#"0xf625ce04"> = <#"Hello">
#	endscript
#	""", params)
#	assert qb is not None
#	assert qb.to_file('./tests/data/Example.qb', params)

#def test_hash_strings():
#	qb = QB.from_string("""
#	script #"TestHashStrings"
#		#"some value" = #"0xffffffff"
#		#"some thing" = <#"some value">
#		#"some thing" = <#"0xcc489b50">
#	endscript
#	""", params)
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
#	""", params)
#	assert qb is not None
#	assert qb.to_file('./tests/data/Example.qb', params)

# def test_random_no_repeat():
# 	qb = QB.from_string("""
# 	RandomNoRepeat(
# 		@Obj_PlaySound BailBodyPunch01_11 pitch = (80.0,102.0) vol = (100.0,120.0)
# 		@Obj_PlaySound BailBodyPunch02_11 pitch = (80.0,102.0) vol = (100.0,120.0)
# 		@Obj_PlaySound BailBodyPunch03_11 pitch = (80.0,102.0) vol = (100.0,120.0)
# 		@Obj_PlaySound BailBodyPunch04_11 pitch = (80.0,102.0) vol = (100.0,120.0)
# 		@Obj_PlaySound BailBodyPunch05_11 pitch = (80.0,102.0) vol = (100.0,120.0)
# 	)
# 	""", params)
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
# 	""", params)
# 	assert qb is not None

# 	qb = QB.from_string('wait RandomNoRepeat(@0.1 @0.14 @0.2 @0.25 @0.28 @0.34) seconds', params)
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
#	qb = QB.from_string(source, params)
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
