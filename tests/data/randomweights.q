script RandomNoRepeatTest
	RandomNoRepeat(
		@Obj_PlaySound RU_BellHit01 vol = 50 pitch = 100 emitter = TRG_SFX_SOB_BigBellsRing01
		@Obj_PlaySound RU_BellHit01 vol = 80 pitch = 50 emitter = TRG_SFX_SOB_BigBellsRing01
		@*5 Obj_PlaySound RU_BellHit01 vol = 30 pitch = 150 emitter = TRG_SFX_SOB_BigBellsRing01
		@*5 Obj_PlaySound RU_BellHit01 vol = 30 pitch = 150 emitter = TRG_SFX_SOB_BigBellsRing01
		@*2 Obj_PlaySound RU_BellHit01 vol = 50 pitch = 94.41000366 emitter = TRG_SFX_SOB_BigBellsRing01
		@*4 Obj_PlaySound RU_BellHit01 vol = 60 pitch = 75 emitter = TRG_SFX_SOB_BigBellsRing01
		@*2 Obj_PlaySound RU_BellHit01 vol = 25 pitch = 200 emitter = TRG_SFX_SOB_BigBellsRing01
	)
endscript