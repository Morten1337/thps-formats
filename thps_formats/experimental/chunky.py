import os
import sys
import json
from enum import Enum, IntEnum
from pathlib import Path as Path
from thps_formats.utils.reader import BinaryReader


# -------------------------------------------------------------------------------------------------
TMP = {'world_flags': 0} # @tmp hack


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
class WorldFlags(IntEnum):
	TRISTRIP = 0x00000001 # This world's meshes can be rendered as tri strips
	POSITIONS = 0x00000002 # This world has positions
	TEXTURED = 0x00000004 # This world has only one set of texture coordinates
	PRELIT = 0x00000008 # This world has luminance values
	NORMALS = 0x00000010 # This world has normals
	LIGHT = 0x00000020 # This world will be lit 🔥
	MODULATE_MATERIAL_COLOR = 0x00000040 # Modulate material color with vertex colors (pre-lit + lit)
	TEXTURED2 = 0x00000080 # This world has 2 or more sets of texture coordinates

	NATIVE = 0x01000000
	NATIVE_INSTANCE = 0x02000000
	FLAGS_MASK = 0x000000FF
	NATIVE_FLAGS_MASK = 0x0F000000
	SECTORS_OVERLAP = 0x40000000


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
	CollisionTHPS		= 0x000001AF # thps3 PLG
	BinMesh				= 0x0000050E # faceset/mesh/matsplit

	CollisionFaceFlag	= 0x0294AF01 # thps3 extension
	Unknown1			= 0x0294AF04 # thps3 extension


# -------------------------------------------------------------------------------------------------
def process_chunk(br, parent=None):

	chunk = Chunk().read(br, parent)

	#print('reading chunk', chunk.get_type())

	# handle struct chunks and de-serialize them
	if chunk.get_type() == ChunkType.Struct:

		chunk.raw = br.read_bytes(chunk.get_size())
		parser = BinaryReader(chunk.raw)
		if parent.get_type() == ChunkType.World:
			chunk.struct = WorldStruct(parser)
		elif parent.get_type() == ChunkType.MaterialList:
			chunk.struct = MaterialListStruct(parser)
		elif parent.get_type() == ChunkType.AtomicSection:
			chunk.struct = AtomicSectionStruct(parser)
		elif parent.get_type() == ChunkType.PlaneSection:
			# ehh, we just discard this later anyways...
			# as we're only interested in the atomic sections 
			pass
		else:
			#raise NotImplementedError(f'Unhandled Struct for {parent.get_type()}')
			print(f'Skip parsing struct for {parent.get_type()} with size {chunk.get_size()} at {chunk.get_start()}...')

	# handle strings separately... @todo: unicode strings
	elif chunk.get_type() == ChunkType.String:
		chunk.string = br.read_bytes(chunk.get_size())

	# handle nested chunks
	elif chunk.is_container():
		while (br.stream.tell() < chunk.get_start() + chunk.get_size()):
			tmp = process_chunk(br, chunk)
			chunk.chunks.append(tmp)

	# handle remaining chunks... @todo: de-serialize
	else:
		chunk.raw = br.read_bytes(chunk.get_size())

	return chunk


# -------------------------------------------------------------------------------------------------
class Struct(object):
	def toJSON(self):
		result = {}
		for attr, value in self.__dict__.items():
			result[attr] = value
		return result


# -------------------------------------------------------------------------------------------------
class WorldStruct(Struct):
	def __init__(self, br):
		super().__init__()
		self.unk00 = br.read_uint32()
		self.unk04 = br.read_float()
		self.unk08 = br.read_float()
		self.unk12 = br.read_float()
		self.unk16 = br.read_float()
		self.unk20 = br.read_uint32()
		self.num_triangles = br.read_uint32()
		self.num_vertices = br.read_uint32()
		self.num_planes = br.read_uint32()
		self.num_atomics = br.read_uint32()
		self.unk44 = br.read_uint32()
		self.world_flags = br.read_uint32()
		TMP['world_flags'] = self.world_flags # @tmp hack


# -------------------------------------------------------------------------------------------------
class MaterialListStruct(Struct):
	def __init__(self, br):
		super().__init__()
		self.num_materials = br.read_uint32()
		assert self.num_materials == 255 # @testing, ap.bsp
		# skipping the material instance stuff
		br.seek(self.num_materials * 4, os.SEEK_CUR)


# -------------------------------------------------------------------------------------------------
class AtomicSectionStruct(Struct):
	def __init__(self, br):
		super().__init__()
		self.unk00 = br.read_uint32() # @todo, always null?
		self.num_faces = br.read_uint32()
		self.num_verts = br.read_uint32()
		self.bbox = [br.read_float() for _ in range(6)]
		self.unk32 = br.read_uint32() # @todo
		self.unk36 = br.read_uint32() # @todo
		self.vertices = [br.read_vec3() for _ in range(self.num_verts)]
		if (TMP['world_flags'] & WorldFlags.NORMALS):
			br.seek(self.num_verts * 4, os.SEEK_CUR)
		self.colors = [br.read_uint32() for _ in range(self.num_verts)]
		self.uvs = [br.read_vec2() for _ in range(self.num_verts)]
		if any([
			(TMP['world_flags'] & WorldFlags.MODULATE_MATERIAL_COLOR),
			(TMP['world_flags'] & WorldFlags.TEXTURED2)
		]):
			br.seek(self.num_verts * 8, os.SEEK_CUR)
		# @todo
		# self.collision = [[br.read_uint16() for _ in range(4)] for _ in range(self.num_faces)]


# -------------------------------------------------------------------------------------------------
class Chunk(object):
	"""
		For de-serialized the MaterialList Struct-chunk
	"""
	raw = None
	struct = None
	string = None

	def __init__(self):
		pass

	# parse chunk header from stream
	def read(self, br, parent=None):
		# read the header
		self.start = br.stream.tell() # useful
		self.type = ChunkType(br.read_uint32())
		self.size = br.read_uint32()
		self.version = br.read_uint32()
		assert self.version == 0x00000310
		# some chunks have multiple sub chunks, so parse these individually!
		# some chunks also have their own data, although in most cases it's stored in a Struct chunk...
		self.chunks = []
		# might be useful
		self.parent = parent
		return self

	# for debugging 
	def toJSON(self):
		result = {'type': str(self.type), 'size': self.size}
		if len(self.chunks) > 0:
			result['chunks'] = [chunk.toJSON() for chunk in self.chunks]
		elif self.type == ChunkType.Struct:
			if self.struct is not None:
				result['struct'] = self.struct.toJSON()
			result['raw'] = self.raw.hex()
		elif self.type == ChunkType.String:
			result['string'] = str(self.string)
		elif self.raw is not None:
			result['raw'] = self.raw.hex()

		return result

	# whether this chunk contains other chunks
	def is_container(self):
		return (self.type in [
			ChunkType.Extension,
			ChunkType.MaterialList,
			ChunkType.Material,
			ChunkType.Texture,
			ChunkType.PlaneSection,
			ChunkType.AtomicSection,
			ChunkType.World,
		])

	# 
	def get_parent(self):
		return self.parent

	# 
	def get_type(self):
		return self.type

	# 
	def get_size(self):
		return self.size

	# 
	def get_version(self):
		return self.version

	# 
	def get_start(self):
		return self.start


# -------------------------------------------------------------------------------------------------
def to_scene(root, filename):

	def flatten_binary_tree(root):

		if root.get_type() == ChunkType.AtomicSection:
			return [root]

		result = []
		for chunk in root.chunks:
			result.extend(flatten_binary_tree(chunk))

		return result

	# -- flatten plane sections
	plane = find_first_chunk_of_type(root.chunks, ChunkType.PlaneSection)
	assert plane.get_type() == ChunkType.PlaneSection
	atomics = flatten_binary_tree(plane)
	root.chunks.remove(plane)
	root.chunks.extend(atomics)

	# -- debug
	with open('./tests/data/ap.json', 'w') as out:
		json.dump(root.toJSON(), out, indent=4)

	# -- debug
	with open('./tests/data/ap-atomics.json', 'w') as out:
		json.dump([chunk.toJSON() for chunk in atomics], out, indent=4)

	def handle_materials(root):
		container = find_first_chunk_of_type(root.chunks, ChunkType.MaterialList)
		materials = find_chunks_by_type(container.chunks, ChunkType.Material)
	#	print(container)
	#	print(materials)

	def handle_objects(root):
		pass

	handle_materials(root)
	handle_objects(root)


# -------------------------------------------------------------------------------------------------
sys.setrecursionlimit(2048 * 2)

# steps/todo:
# - recursively read chunks
# 	- de-serialize structs
# 	- de-serialize other chunks
# - flatten plane section 
# - convert to shared scene structure


# -------------------------------------------------------------------------------------------------
def Chunky(filename):

	pathname = Path(filename).resolve()
	with open(pathname, 'rb') as inp:

		# create an an instance of our reader class
		br = BinaryReader(inp)

		root = process_chunk(br, None)
		assert root.get_type() == ChunkType.World

		to_scene(root, 'ap.scn.xbx')

		return root
