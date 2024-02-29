//#define __SUPPORT_RANDOM__

complex=0/*
comment
comment
*/hello = 0

GlobalName = animload_THPS6_human
GlobalString = "Water: Main Level"
GlobalVec3 = (3.14159298,-0.75049102,3.14159298)
GlobalVec2 = (0.00000000,1.00000000)
GlobalSimpleArray = [MultiPlayer Horse]
GlobalInteger = 1234 // inline comment
GlobalFloat = 3.14159298

//invalid = asfa"

; alt style comment
// normal style comment

NodeArray =
[
	{
		Pos = (3868.65771484,0.0,653.70922852)
		Angles = (0.0,-1.57079601,0.0)
		Name = TRG_BA_Rail01
		ncomp_RailNode_1
		Links = [1]
	}
/*
	{
		Pos = (3460.84301758,1227.33447266,2315.26611328)
		Angles = (0.0,0.0,0.0)
		Name = TRG_BA_Pigeon03
		ncomp_Pedestrian_1821
		TriggerScript = TRG_BA_Pigeon03Script
	}*/
	{
		Pos = (3550.87084961,-0.000008,2433.00634766)
		Angles = (3.14159298,-0.78539801,3.14159298)
		Name = TRG_BA_Restart_Water01
		Class = Restart
		Type = Generic
		CreatedAtStart
		RestartName = "Water: Main Level"
		LocalName = "Main Level"
		restart_types = [MultiPlayer Horse]
	}
]

// simple comment
ncomp_Pedestrian_1821 = {
	Class = Pedestrian
	Type = Anl_Pigeon
	CreatedAtStart
	AbsentInNetGames
	PedAI_Type = Stand
	SkeletonName = Anl_Pigeon
	AnimName = animload_anl_pigeon
	model = "animals\anl_pigeon\anl_pigeon.skin"
	SuspendDistance = 0
	lod_dist1 = 100
	lod_dist2 = 400
}

script load_level_anims {
	CallbackFunction = NullScript
}
	animload_THPS6_human
	animload_ped_female
	animload_PED_Mime
	animload_anl_bull
	animload_anl_pigeon
	animload_THPS6_Veh_Bull
	animload_Ped_M_Pissed
	<CallbackFunction> Test
endscript
script LoadCameras
	LoadAsset "levels\ba\CAM_Classic_Intro01.ska" desc = CAM_Classic_Intro01
endscript
script LoadObjectAnims
endscript


script TRG_BA_Pigeon03Script

	BA_Phoenix

	if (<something> == 1)
		<something> = 0
	endif

	if (((GetGlobalFlag flag = FLAG_EXPERT_MODE_NO_MANUALS) OR (GetGlobalFlag flag = FLAG_G_EXPERT_MODE_NO_MANUALS))
	OR ((GetGlobalFlag flag = FLAG_EXPERT_MODE_NO_REVERTS) OR (GetGlobalFlag flag = FLAG_G_EXPERT_MODE_NO_REVERTS)))
		// No land pivots when reverts or manuals are disabled...
	else
		GetSpeed
		if (<speed> > 250)
			SetExtraTricks tricks = LandPivot Duration = <RevertTime>
		endif
	endif

//	SHIFTRIGHT = (0 >> 1)
//	SHIFTLEFT = (0 << 1)

	if (GREATERTHANEQUAL >= 0)
	endif

	if (LESSTHANEQUAL <= 0)
	endif

	if (GREATERTHAN > 0)
	endif

	if (LESSTHAN < 0)
	endif

	nullscript <...>
	nullscript params = <argument>

	<TempVec3> = (3.14159298, -0.75049102,3)
	<TempVec2> = (0.00000000, 1.00000000)
//	<TempVec4> = (0.00000000, 1.00000000, 5.00000000, 3.00000000)
//	<TempInvalid> = (1.-9999999,.3,.4)
endscript

array_with_commas = [0,1,2,3,4,5,6,7,8]

script LogicalTest
	<test> = 2

	if ((<test> == 1) || (<test> == 2))
	endif

	if ((<test> > 0) || (<test> < 3))
	endif
endscript

script ColonTest
	<ObjID>::Obj_GetTags
endscript


GlobalInteger = 1
GlobalInteger = 0
GlobalInteger = -32959325
GlobalFloat = .241245
GlobalFloat = 0.0
GlobalFloat = -1300.0
GlobalVector = (3.14159298, -0.75049102,3)
GlobalVector = (0.00000000, 1.00000000)


script ArithmeticTest
	<test> = -1
	<test> = (<test> + 10)
	<test> = (<test> - 5)
	<test> = (<test> * 100)
	<test> = (<test> / 2)
	<test> = (<test> + -10)
	<test> = (<test> - -5)
endscript

script DotTest
	scale = .1
	font_face = ((THUGPRO_GlobalThemeInfo).PANEL_MESSAGE_FONT)
	scale = 0.01
endscript

script NanTest
	scale = NaN
	scale = nan
	scale = NAN
endscript

script AtTest
#ifdef __SUPPORT_RANDOM__
	RandomNoRepeat(
		@Obj_PlaySound SK6_BA_BullGallop01 vol = 80 dropoff = 150
		@Obj_PlaySound SK6_BA_BullGallop02 vol = 80 dropoff = 150
		@Obj_PlaySound SK6_BA_BullGallop03 vol = 80 dropoff = 150
		@Obj_PlaySound SK6_BA_BullGallop04 vol = 80 dropoff = 150
	)
#endif // __SUPPORT_RANDOM__
endscript

script HashTest
	// this is fine
	#"this is fine" = STR_CHECKSUM
	#"0x00000000" = HEX_CHECKSUM
	// this is also fine, but i dont handle it properly
	STR_CHECKSUM = <#"this is fine">
	HEX_CHECKSUM = <#"0xffffffff">
endscript

script JumpTest
	#goto End
	print "Skipped"
End:
	print "Ending"
endscript

#include "tests\data\include.q"
//#include "..\thugpro\source\generated\levelselect\levelselect_thaw.q"
//#include "..\thugpro\source\generated\levelselect\levelselect_thug2.q"

#define DEVELOPER
#define THUGPRO_MENU_ITEM_DEBUG

#ifdef DEVELOPER
	#ifdef THUGPRO_MENU_ITEM_DEBUG
		Something = hello
		Something = hello
		Something = hello
		Something = hello
	#else
		Something = howdy
		Something = howdy
		Something = howdy
	#endif
#endif

#ifndef DEVELOPER
	Ignored
	Ignored
	Ignored
	Ignored
#else
	#ifndef THUGPRO_MENU_ITEM_DEBUG
		IgnoredTOo
		IgnoredTOo
		IgnoredTOo
		IgnoredTOo
	#else
		Helloooo
		Helloooo
		Helloooo
		Helloooo
	#endif
#endif

script OperatorTest
//	something = 0 >> 1
//	something = 0 << 1
//	something = 0 | 1 ; fail
//	something = 0 & 1 ; fail
endscript

script HexTest
	#"0xf625ce04" = 0x00000000
	#"0x738c9ade" = <#"0xf625ce04">
endscript

//GlobalRandomInvalid = RandomRange(0.1,3.0) ; fail
script RandomTest
//	Obj_PlaySound {
//		vol = RandomRange(0.1,3.0)
//		pitch = RandomRange2(1,40)
//	}
	Something = RandomRange(1,2)
endscript

script #"ScriptTest"
	Hello
endscript

script #"0x6af56176"
	Hello
endscript

//script "ScriptTest" ; fail
//	Hello
//endscript

//script /* ; fail
//	Hello
//	*/
//endscript

script ReturnTest
	Hello
//	break
	return { Something = 1234 }
endscript

script SwitchTest

	switch <next_tod>
		case morning
			next_tod_string = "Morning"
		case afternoon
			next_tod_string = "Day"
		case evening
			next_tod_string = "Evening"
		case night
			next_tod_string = "Night"
		default
			next_tod_string = "Day"
	endswitch

	switch (tod_current_state)
		case morning
			current_tod_string = "Morning"
		case afternoon
			current_tod_string = "Day"
		case evening
			current_tod_string = "Evening"
		case night
			current_tod_string = "Night"
		default
			current_tod_string = "Day"
	endswitch

	Change tod_current_state = <next_tod>
	return current_tod_string = <current_tod_string> next_tod_string = <next_tod_string>

endscript