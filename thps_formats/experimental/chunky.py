import os
from enum import Enum
from pathlib import Path as Path
from thps_formats.utils.reader import BinaryReader


# -------------------------------------------------------------------------------------------------
def count_chunks_of_type(chunks, chunk_type):
	return sum(1 for chunk in chunks if chunk.get_type() == chunk_type)


# -------------------------------------------------------------------------------------------------
def find_chunks_by_type(chunks, chunk_type):
	return [chunk for chunk in chunks if chunk.get_type() == chunk_type]


# -------------------------------------------------------------------------------------------------
def find_first_chunk_of_type(chunks, chunk_type):
	return next((chunk for chunk in chunks if chunk.get_type() == chunk_type), None)


# -------------------------------------------------------------------------------------------------
# https://gtamods.com/wiki/List_of_RW_section_IDs
class ChunkType(Enum):

	Struct				= 0x00000001 # A generic section that stores data for its parent.
	String				= 0x00000002 # Stores a 4-byte aligned ASCII string.
	Extension			= 0x00000003 # A container for non-standard extensions of its parent section.

	Camera				= 0x00000005 # Contains a camera (possibly unused).
	Texture				= 0x00000006 # Stores the sampler state of a texture.
	Material			= 0x00000007 # Defines a material to be used on a geometry.
	MaterialList		= 0x00000008 # Container for a list of materials.
	AtomicSection		= 0x00000009
	PlaneSection		= 0x0000000A
	World				= 0x0000000B # The root section of the level geometry.
	Spline				= 0x0000000C
	Matrix				= 0x0000000D
	FrameList			= 0x0000000E # Container for a list of frames. A frame holds the transformation that is applied to an Atomic.
	Geometry			= 0x0000000F # A platform-independent container for meshes.
	Clump				= 0x00000010 # The root section for a 3D model.
	Light				= 0x00000012 # Stores different dynamic lights.
	UnicodeString		= 0x00000013
	Atomic				= 0x00000014 # Defines the basic unit for the RenderWare graphics pipeline. Generally speaking, an Atomic can be directly converted to a single draw call.
	Raster				= 0x00000015 # Stores a platform-dependent (i.e. native) texture image.
	TextureDictionary	= 0x00000016 # A container for texture images (also called raster).
	AnimationDatabase	= 0x00000017
	Image				= 0x00000018
	SkinAnimation		= 0x00000019
	GeometryList		= 0x0000001A # A container for a list of geometries.
	# @todo ...
	MaterialEffects		= 0x00000120
	Collision			= 0x0000011D
	CollisionTHPS		= 0x000001AF
	BinMesh				= 0x0000050E # faceset/mesh/matsplit
	CollisionFaceFlag	= 0x0294AF01 # thps3 extension


def read_chunk(br):

	chunk = Chunk().read(br)

	print('reading chunk', chunk.get_type())

	if chunk.get_type() == ChunkType.Struct:
		return StructChunk(chunk).read(br)

	elif chunk.get_type() == ChunkType.MaterialList:
		return MaterialListChunk(chunk).read(br)

	elif chunk.get_type() == ChunkType.Material:
		return MaterialChunk(chunk).read(br)

	elif chunk.get_type() == ChunkType.World:
		return WorldChunk(chunk).read(br)

	elif chunk.get_type() == ChunkType.Clump:
		return ClumpChunk(chunk).read(br)

	else:
		#raise NotImplementedError(f'Unhandled Chunk type {chunk.get_type()}')
		print(f'skipping unknown chunk type {chunk.get_type()} with size {chunk.get_size()} at {chunk.get_start()}...')
		chunk.data = br.read_bytes(chunk.get_size())
		return chunk


class Chunk(object):

	def __init__(self):
		pass

	def read(self, br):
		# read the header
		self.start = br.stream.tell() # useful
		self.type = ChunkType(br.read_uint32())
		self.size = br.read_uint32()
		self.version = br.read_uint32()
		# some chunks have multiple sub chunks, so parse these induvidually!
		# some chunks also have their own data, although in most cases it's stored in a Struct chunk...
		self.chunks = []

		return self

	def get_type(self):
		return self.type

	def get_size(self):
		return self.size

	def get_version(self):
		return self.version

	def get_start(self):
		return self.start


# generic data
class StructChunk(Chunk):

	data = None # @tmp

	def __init__(self, base):
		super().__init__()
		self.__dict__.update(base.__dict__)

	def read(self, br):
		self.data = br.read_bytes(self.size)
		return self


# material
class MaterialChunk(Chunk):

	data = None # @tmp

	def __init__(self, base):
		super().__init__()
		self.__dict__.update(base.__dict__)

	def read(self, br):
		self.data = br.read_bytes(self.size)
		return self


# Material List
class MaterialListChunk(Chunk):

	num_materials = -1 # @tmp

	def __init__(self, base):
		super().__init__()
		self.__dict__.update(base.__dict__)

	def read(self, br):

		struct = read_chunk(br)
		assert struct.get_type() == ChunkType.Struct
		self.chunks.append(struct)
		
		parser = BinaryReader(struct.data)
		self.num_materials = parser.read_uint32()
		assert self.num_materials == 255 # @testing, ap.bsp
		parser.seek(self.num_materials * 4, os.SEEK_CUR) # @note, skip the junk

		while (br.stream.tell() < self.start + self.size):
			material = read_chunk(br)
			assert material.get_type() == ChunkType.Material
			self.chunks.append(material) # should just be material chunks now

		assert count_chunks_of_type(self.chunks, ChunkType.Material) == self.num_materials

		return self


# bsp root
class WorldChunk(Chunk):

	world_flag = -1

	def __init__(self, base):
		super().__init__()
		self.__dict__.update(base.__dict__)

	def read(self, br):

		struct = read_chunk(br)
		assert struct.get_type() == ChunkType.Struct
		self.chunks.append(struct)
		
		parser = BinaryReader(struct.data)
		parser.seek(48, os.SEEK_CUR) # @todo, skippin 30 bytes
		self.world_flag = parser.read_uint32()
		assert self.world_flag == 0x400200c9 # @testing, ap.bsp

		#matlist = read_chunk(br)
		#assert matlist.get_type() == ChunkType.MaterialList

		while (br.stream.tell() < self.start + self.size):
			self.chunks.append(read_chunk(br))

		return self


# dff root
class ClumpChunk(Chunk):

	def __init__(self, base):
		super().__init__()
		self.__dict__.update(base.__dict__)

	def read(self, br):
		return self


def to_collision(root, filename):
	pass


def to_scene(root, filename):

	def handle_materials(root):
		container = find_first_chunk_of_type(root.chunks, ChunkType.MaterialList)
		materials = find_chunks_by_type(container.chunks, ChunkType.Material)
	#	print(container)
	#	print(materials)

	def handle_objects(root):
		pass

	handle_materials(root)
	handle_objects(root)
	pass


def Chunky(filename):

	pathname = Path(filename).resolve()

	with open(pathname, 'rb') as inp:

		# create an an instance of our reader class
		br = BinaryReader(inp)

		root = read_chunk(br)
		assert root.get_type() == ChunkType.World

		to_scene(root, 'ap.scn.xbx')

		return root
