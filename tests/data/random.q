script FL_SFX_GarageWarp01
	RandomNoRepeat(
		@Obj_PlayStream FL_ParkingGarageHorn01 emitter = TRG_SFX_SOB_GarageWarp01
		@Obj_PlayStream FL_ParkingGarageHorn02 emitter = TRG_SFX_SOB_GarageWarp01
		@Obj_PlayStream FL_ParkingGarageHorn03 emitter = TRG_SFX_SOB_GarageWarp01
		@Obj_PlayStream FL_ParkingGarageHorn04 emitter = TRG_SFX_SOB_GarageWarp01
	)
endscript
//script PlayWalkStandAnim
//	while
//		PlayWalkAnim BlendPeriod = 0.1 Anim = Random(@*3 WStand @RandomNoRepeat(@WStandIdle1 @WStandIdle2 @WStandIdle3 @WStandIdle4 @WStandIdle5 @WStandIdle6))
//		WaitAnimWalking
//	repeat
//endscript
//script ALF_Ped_BailWhenSkaterClose
//	Obj_ClearExceptions
//	Random(
//		@Obj_CycleAnim anim = Ped_M_FalldownA
//		Obj_PlayAnim anim = Ped_M_LayIdleA cycle
//		SetTags Bail = A
//		@Obj_CycleAnim anim = Ped_M_FalldownB
//		Obj_PlayAnim anim = Ped_M_LayIdleB cycle
//		SetTags Bail = B
//		@Obj_CycleAnim anim = Ped_M_FalldownC
//		Obj_PlayAnim anim = Ped_M_LayIdleC cycle
//		SetTags Bail = C
//		@Obj_CycleAnim anim = Ped_M_FalldownD
//		Obj_PlayAnim anim = Ped_M_LayIdleD cycle
//		SetTags Bail = D
//		@Obj_CycleAnim anim = Ped_M_FalldownE
//		Obj_PlayAnim anim = Ped_M_LayIdleE cycle
//		SetTags Bail = E
//	)
//	Obj_SetException ex = ObjectOutofRadius scr = ALF_Ped_GetUpFromBail
//	Obj_SetOuterRadius 10
//endscript
