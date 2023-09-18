from thps_formats.experimental import Chunky, ChunkType


# def test_bsp():
# 	root = Chunky('./tests/data/ap.bsp')
# 	assert root.get_type() == ChunkType.WORLD


def test_dff():
	root = Chunky('./tests/data/ap.dff')
	assert len(root) > 0
	assert root[0].get_type() == ChunkType.CLUMP


# def test_dff2():
# 	root = Chunky('./tests/data/low_rider.dff')
# 	assert len(root) > 0
# 	assert root[0].get_type() == ChunkType.CLUMP


# def test_tdx():
# 	root = Chunky('./tests/data/ap.tdx')
# 	assert root.get_type() == ChunkType.TEXDICTIONARY


# def test_skn():
# 	root = Chunky('./tests/data/ped_bum_a.skn')
# 	assert root.get_type() == ChunkType.CLUMP
