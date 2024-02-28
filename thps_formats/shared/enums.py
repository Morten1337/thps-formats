from functools import total_ordering
from enum import Enum, auto

# @note: I don't know about all this... Maybe it's a bit too much???


# -------------------------------------------------------------------------------------------------
class PlatformType(Enum):
	# Default
	NONE = auto()
	# Microsoft
	WIN = auto()
	XBX = auto()
	XEN = auto()
	# Sony
	PS1 = auto()
	PS2 = auto()
	PSP = auto()
	PS3 = auto()
	# Nintendo
	N64 = auto()
	NGC = auto()
	WII = auto()
	# Seegaaaa...
	DC = auto()


# -------------------------------------------------------------------------------------------------
@total_ordering
class GameType(Enum):
	# Default
	NONE = (0, 0)
	# Main games
	THPS1 = (1, 0)
	THPS2 = (2, 0)
	THPS3 = (3, 0)
	THPS4 = (4, 0)
	THUG1 = (5, 0)
	THUG2 = (6, 0)
	THAW = (7, 0)
	THDJ = (7, 0)
	THP8 = (8, 0)
	THPG = (8, 0)
	# Various
	DESA = (4, 1)
	MTX = (5, 1)
	MG = (5, 2)
	THUGPRO = (6, 1)
	GUN = (7, 2)

	# ---------------------------------------------------------------------------------------------
	def __lt__(self, other):
		if self.__class__ is other.__class__:
			return self.value < other.value
		return NotImplemented

	# ---------------------------------------------------------------------------------------------
	def __eq__(self, other):
		if self.__class__ is other.__class__:
			return self.value == other.value
		return NotImplemented


# -------------------------------------------------------------------------------------------------
class GameVersion(Enum):
	# Default
	NONE = (GameType.NONE, PlatformType.NONE)
	# Tony Hawk's Pro Skater
	THPS1_PS1 = (GameType.THPS1, PlatformType.PS1)
	THPS1_N64 = (GameType.THPS1, PlatformType.N64)
	THPS1_DC = (GameType.THPS1, PlatformType.DC)
	# Tony Hawk's Pro Skater 2
	THPS2_WIN = (GameType.THPS2, PlatformType.WIN)
	THPS2_XBX = (GameType.THPS2, PlatformType.XBX) # THPS2x
	THPS2_PS1 = (GameType.THPS2, PlatformType.PS1)
	THPS2_N64 = (GameType.THPS2, PlatformType.N64)
	THPS2_DC = (GameType.THPS2, PlatformType.DC)
	# Tony Hawk's Pro Skater 3
	THPS3_WIN = (GameType.THPS3, PlatformType.WIN)
	THPS3_XBX = (GameType.THPS3, PlatformType.XBX)
	THPS3_PS1 = (GameType.THPS3, PlatformType.PS1)
	THPS3_PS2 = (GameType.THPS3, PlatformType.PS2)
	THPS3_N64 = (GameType.THPS3, PlatformType.N64)
	THPS3_NGC = (GameType.THPS3, PlatformType.NGC)
	# Tony Hawk's Pro Skater 4
	THPS4_WIN = (GameType.THPS4, PlatformType.WIN)
	THPS4_XBX = (GameType.THPS4, PlatformType.XBX)
	THPS4_PS1 = (GameType.THPS4, PlatformType.PS1)
	THPS4_PS2 = (GameType.THPS4, PlatformType.PS2)
	THPS4_NGC = (GameType.THPS4, PlatformType.NGC)
	# Tony Hawk's Underground 1
	THUG1_WIN = (GameType.THUG1, PlatformType.WIN)
	THUG1_XBX = (GameType.THUG1, PlatformType.XBX)
	THUG1_PS2 = (GameType.THUG1, PlatformType.PS2)
	THUG1_NGC = (GameType.THUG1, PlatformType.NGC)
	# Tony Hawk's Underground 2
	THUG2_WIN = (GameType.THUG2, PlatformType.WIN)
	THUG2_XBX = (GameType.THUG2, PlatformType.XBX)
	THUG2_PS2 = (GameType.THUG2, PlatformType.PS2)
	THUG2_PSP = (GameType.THUG2, PlatformType.PSP) # THUG2 Remix
	THUG2_NGC = (GameType.THUG2, PlatformType.NGC)
	# Tony Hawk's American Wasteland
	THAW_WIN = (GameType.THAW, PlatformType.WIN)
	THAW_XBX = (GameType.THAW, PlatformType.XBX)
	THAW_XEN = (GameType.THAW, PlatformType.XEN)
	THAW_PS2 = (GameType.THAW, PlatformType.PS2)
	THAW_NGC = (GameType.THAW, PlatformType.NGC)
	# Tony Hawk's Project 8
	THP8_XBX = (GameType.THP8, PlatformType.XBX)
	THP8_XEN = (GameType.THP8, PlatformType.XEN)
	THP8_PS2 = (GameType.THP8, PlatformType.PS2)
	THP8_PS3 = (GameType.THP8, PlatformType.PS3)
	THP8_PSP = (GameType.THP8, PlatformType.PSP)
	# Tony Hawk's Proving Ground
	THPG_XEN = (GameType.THPG, PlatformType.XEN)
	THPG_PS2 = (GameType.THPG, PlatformType.PS2)
	THPG_PS3 = (GameType.THPG, PlatformType.PS3)
	THPG_WII = (GameType.THPG, PlatformType.WII)
	# THUG PRO
	THUGPRO_WIN = (GameType.THUGPRO, PlatformType.WIN)
	# Disney's Extreme Skate Adventure
	DESA_XBX = (GameType.DESA, PlatformType.XBX)
	DESA_PS2 = (GameType.DESA, PlatformType.PS2)
	DESA_NGC = (GameType.DESA, PlatformType.NGC)
	# MTX Mototrax
	MTX_WIN = (GameType.MTX, PlatformType.WIN)
	MTX_XBX = (GameType.MTX, PlatformType.XBX)
	MTX_PS2 = (GameType.MTX, PlatformType.PS2)
	MTX_PSP = (GameType.MTX, PlatformType.PSP)
	# Monster Garage
	MG_XBX = (GameType.MG, PlatformType.XBX)
	# Tony Hawk's Downhill Jam
	THDJ_PS2 = (GameType.THDJ, PlatformType.PS2)
	THDJ_WII = (GameType.THDJ, PlatformType.WII)
	# GUN
	GUN_WIN = (GameType.GUN, PlatformType.WIN)
	GUN_XBX = (GameType.GUN, PlatformType.XBX)
	GUN_XEN = (GameType.GUN, PlatformType.XEN)
	GUN_PS2 = (GameType.GUN, PlatformType.PS2)
	GUN_NGC = (GameType.GUN, PlatformType.NGC)
