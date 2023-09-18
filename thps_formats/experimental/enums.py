from enum import Enum


# -------------------------------------------------------------------------------------------------
class ChunkType(Enum):
	# Core
	NAOBJECT			= 0x00000000
	STRUCT				= 0x00000001
	STRING				= 0x00000002
	EXTENSION			= 0x00000003
	CAMERA				= 0x00000005
	TEXTURE				= 0x00000006
	MATERIAL			= 0x00000007
	MATLIST				= 0x00000008
	ATOMICSECT			= 0x00000009
	PLANESECT			= 0x0000000A
	WORLD				= 0x0000000B
	SPLINE				= 0x0000000C
	MATRIX				= 0x0000000D
	FRAMELIST			= 0x0000000E
	GEOMETRY			= 0x0000000F
	CLUMP				= 0x00000010
	LIGHT				= 0x00000012
	UNICODESTRING		= 0x00000013
	ATOMIC				= 0x00000014
	TEXTURENATIVE		= 0x00000015
	TEXDICTIONARY		= 0x00000016
	ANIMDATABASE		= 0x00000017
	IMAGE				= 0x00000018
	SKINANIMATION		= 0x00000019
	GEOMETRYLIST		= 0x0000001A
	ANIMANIMATION		= 0x0000001B
	HANIMANIMATION		= 0x0000001B
	TEAM				= 0x0000001C
	CROWD				= 0x0000001D
	DMORPHANIMATION		= 0x0000001E
	RIGHTTORENDER		= 0x0000001f
	MTEFFECTNATIVE		= 0x00000020
	MTEFFECTDICT		= 0x00000021
	TEAMDICTIONARY		= 0x00000022
	PITEXDICTIONARY		= 0x00000023
	TOC					= 0x00000024
	PRTSTDGLOBALDATA	= 0x00000025
	ALTPIPE				= 0x00000026
	PIPEDS				= 0x00000027
	PATCHMESH			= 0x00000028
	CHUNKGROUPSTART		= 0x00000029
	CHUNKGROUPEND		= 0x0000002A
	UVANIMDICT			= 0x0000002B
	COLLTREE			= 0x0000002C
	ENVIRONMENT			= 0x0000002D
	COREPLUGINIDMAX		= 0x0000002E
	# Toolkit
	METRICSPLUGIN		= 0x00000101
	SPLINEPLUGIN		= 0x00000102
	STEREOPLUGIN		= 0x00000103
	VRMLPLUGIN			= 0x00000104
	MORPHPLUGIN			= 0x00000105
	PVSPLUGIN			= 0x00000106
	MEMLEAKPLUGIN		= 0x00000107
	ANIMPLUGIN			= 0x00000108
	GLOSSPLUGIN			= 0x00000109
	LOGOPLUGIN			= 0x0000010a
	MEMINFOPLUGIN		= 0x0000010b
	RANDOMPLUGIN		= 0x0000010c
	PNGIMAGEPLUGIN		= 0x0000010d
	BONEPLUGIN			= 0x0000010e
	VRMLANIMPLUGIN		= 0x0000010f
	SKYMIPMAPVAL		= 0x00000110
	MRMPLUGIN			= 0x00000111
	LODATMPLUGIN		= 0x00000112
	MEPLUGIN			= 0x00000113
	LTMAPPLUGIN			= 0x00000114
	REFINEPLUGIN		= 0x00000115
	SKINPLUGIN			= 0x00000116
	LABELPLUGIN			= 0x00000117
	PARTICLESPLUGIN		= 0x00000118
	GEOMTXPLUGIN		= 0x00000119
	SYNTHCOREPLUGIN		= 0x0000011a
	STQPPPLUGIN			= 0x0000011b
	PARTPPPLUGIN		= 0x0000011c
	COLLISPLUGIN		= 0x0000011d
	HANIMPLUGIN			= 0x0000011e
	USERDATAPLUGIN		= 0x0000011f
	MATERIALEFFECTSPLUGIN = 0x00000120
	PARTICLESYSTEMPLUGIN = 0x00000121
	DMORPHPLUGIN		= 0x00000122
	PATCHPLUGIN			= 0x00000123
	TEAMPLUGIN			= 0x00000124
	CROWDPPPLUGIN		= 0x00000125
	MIPSPLITPLUGIN		= 0x00000126
	ANISOTPLUGIN		= 0x00000127
	GCNMATPLUGIN		= 0x00000129
	GPVSPLUGIN			= 0x0000012a
	XBOXMATPLUGIN		= 0x0000012b
	MULTITEXPLUGIN		= 0x0000012c
	CHAINPLUGIN			= 0x0000012d
	TOONPLUGIN			= 0x0000012e
	PTANKPLUGIN			= 0x0000012f
	PRTSTDPLUGIN		= 0x00000130
	PDSPLUGIN			= 0x00000131
	PRTADVPLUGIN		= 0x00000132
	NORMMAPPLUGIN		= 0x00000133
	ADCPLUGIN			= 0x00000134
	UVANIMPLUGIN		= 0x00000135
	ENVIRONMENTPLUGIN	= 0x00000136
	CHARSEPLUGIN		= 0x00000180
	NOHSWORLDPLUGIN		= 0x00000181
	IMPUTILPLUGIN		= 0x00000182
	SLERPPLUGIN			= 0x00000183
	OPTIMPLUGIN			= 0x00000184
	TLWORLDPLUGIN		= 0x00000185
	DATABASEPLUGIN		= 0x00000186
	RAYTRACEPLUGIN		= 0x00000187
	RAYPLUGIN			= 0x00000188
	LIBRARYPLUGIN		= 0x00000189
	PLUGIN2D			= 0x00000190
	TILERENDPLUGIN		= 0x00000191
	JPEGIMAGEPLUGIN		= 0x00000192
	TGAIMAGEPLUGIN		= 0x00000193
	GIFIMAGEPLUGIN		= 0x00000194
	QUATPLUGIN			= 0x00000195
	SPLINEPVSPLUGIN		= 0x00000196
	MIPMAPPLUGIN		= 0x00000197
	MIPMAPKPLUGIN		= 0x00000198
	FONT2D				= 0x00000199
	INTSECPLUGIN		= 0x0000019a
	TIFFIMAGEPLUGIN		= 0x0000019b
	PICKPLUGIN			= 0x0000019c
	BMPIMAGEPLUGIN		= 0x0000019d
	RASIMAGEPLUGIN		= 0x0000019e
	SKINFXPLUGIN		= 0x0000019f
	VCATPLUGIN			= 0x000001a0
	PATH2D				= 0x000001a1
	BRUSH2D				= 0x000001a2
	OBJECT2D			= 0x000001a3
	SHAPE2D				= 0x000001a4
	SCENE2D				= 0x000001a5
	PICKREGION2D		= 0x000001a6
	OBJECTSTRING2D		= 0x000001a7
	ANIMPLUGIN2D		= 0x000001a8
	ANIM2D				= 0x000001a9
	KEYFRAME2D			= 0x000001b0
	MAESTRO2D			= 0x000001b1
	BARYCENTRIC			= 0x000001b2
	PITEXDICTIONARYTK	= 0x000001b3
	TOCTOOLKIT			= 0x000001b4
	TPLTOOLKIT			= 0x000001b5
	ALTPIPETOOLKIT		= 0x000001b6
	ANIMTOOLKIT			= 0x000001b7
	SKINSPLITTOOKIT		= 0x000001b8
	CMPKEYTOOLKIT		= 0x000001b9
	GEOMCONDPLUGIN		= 0x000001ba
	WINGPLUGIN			= 0x000001bb
	GENCPIPETOOLKIT		= 0x000001bc
	LTMAPCNVTOOLKIT		= 0x000001bd
	FILESYSTEMPLUGIN	= 0x000001be
	DICTTOOLKIT			= 0x000001bf
	UVANIMLINEAR		= 0x000001c0
	UVANIMPARAM			= 0x000001c1
	# World
	NAWORLDID			= 0x00000500
	MATERIALMODULE		= 0x00000501
	MESHMODULE			= 0x00000502
	GEOMETRYMODULE		= 0x00000503
	CLUMPMODULE			= 0x00000504
	LIGHTMODULE			= 0x00000505
	COLLISIONMODULE		= 0x00000506
	WORLDMODULE			= 0x00000507
	RANDOMMODULE		= 0x00000508
	WORLDOBJMODULE		= 0x00000509
	SECTORMODULE		= 0x0000050A
	BINWORLDMODULE		= 0x0000050B
	WORLDPIPEMODULE		= 0x0000050D
	BINMESHPLUGIN		= 0x0000050E
	RXWORLDDEVICEMODULE = 0x0000050F
	NATIVEDATAPLUGIN	= 0x00000510
	VERTEXFMTPLUGIN		= 0x00000511
	# THPS3
	EXTENSIONTHPS		= 0x0294AF01 # thps3 extension
	EXTENSIONUNK02		= 0x0294AF02 # thps3 dff geo extension
	EXTENSIONUNK03		= 0x0294AF03 # thps3 extension
	EXTENSIONUNK04		= 0x0294AF04 # thps3 bsp world extension
