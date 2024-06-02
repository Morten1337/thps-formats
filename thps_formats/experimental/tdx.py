from . enums import ChunkType
from . chunky import process_chunk
from . utils import (
	find_chunks_with_type,
	find_first_chunk_with_type
)
from thps_formats.utils.reader import BinaryReader
from pathlib import Path as Path


# -------------------------------------------------------------------------------------------------
class TextureContainer:
	pass


# -------------------------------------------------------------------------------------------------
class TDX(TextureContainer):
	def __init__(self, filename):
		super().__init__()
		pathname = Path(filename).resolve()
		extension = pathname.suffix.lower().strip('.')
		scenename = pathname.stem.lower()
		with open(pathname, 'rb') as inp:
			# create an an instance of our reader class
			br = BinaryReader(inp)
			# read teh file
			root = process_chunk(br, None)
			assert root.get_type() == ChunkType.TEXDICTIONARY
			# store in a list for consistency with other rw files
			self.chunks = [root]

	def to_png(self):
		pass


# -------------------------------------------------------------------------------------------------
if __name__ == '__main__':
	tdx = TDX('./tests/data/ap.tdx')
	tdx.to_png('./tests/ap-textures/')
