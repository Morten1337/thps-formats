import os
import sys
import json
from enum import Enum, IntEnum
from pathlib import Path as Path
from thps_formats.utils.reader import BinaryReader
from . enums import ChunkType
from . utils import (
	find_chunks_with_type,
	find_first_chunk_with_type
)


# -------------------------------------------------------------------------------------------------
# https://github.com/Venomalia/RenderWareNET/tree/main/src/RenderWareNET/Plugins
# https://github.com/Struggleton/Amicitia/tree/master/AtlusLibSharp/Graphics/RenderWare
# https://github.com/NanoBob/renderwareio/tree/main/RenderWareIo/Structs
# https://gtamods.com/wiki/List_of_RW_section_IDs

# -------------------------------------------------------------------------------------------------
# steps:
# - recursively read chunks
# 	- de-serialize structs
# 	- de-serialize other chunks
# - flatten plane section 
# - convert to shared scene structure

# todo:
# - material extensions
# - texture extensions
# - triangles??
# - collision and bsp stuff – for completeness 


# -------------------------------------------------------------------------------------------------
def tohex(val, nbits):
	return hex((val + (1 << nbits)) % (1 << nbits))


# -------------------------------------------------------------------------------------------------
class GeometryFlags(IntEnum):
	TRISTRIP = 0x00000001 # This geometry's meshes can be rendered as tri strips
	POSITIONS = 0x00000002 # This geometry has positions  
	TEXTURED = 0x00000004 # This geometry has only one set of texture coordinates
	PRELIT = 0x00000008 # This geometry has pre-light colors
	NORMALS = 0x00000010 # This geometry has vertex normals
	LIGHT = 0x00000020 # This geometry will be lit
	MODULATEMATERIALCOLOR = 0x00000040 # Modulate material color  with vertex colors (pre-lit + lit)
	TEXTURED2 = 0x00000080 # This geometry has at least 2 sets of texture coordinates
	NATIVE = 0x01000000
	NATIVEINSTANCE = 0x02000000
	FLAGSMASK = 0x000000FF
	NATIVEFLAGSMASK = 0x0F000000
	SECTORSOVERLAP = 0x40000000 # World Flag


# -------------------------------------------------------------------------------------------------
class AtomicFlags(IntEnum):
	NONE = 0x00
	COLLISION = 0x01
	RENDER = 0x04


# -------------------------------------------------------------------------------------------------
class MeshHeaderFlags(IntEnum):
	TRILIST = 0x0000
	TRISTRIP = 0x0001
	TRIFAN = 0x0002
	LINELIST = 0x0004
	POLYLINE = 0x0008
	POINTLIST = 0x0010
	UNINDEXED = 0x0100


# -------------------------------------------------------------------------------------------------
class MatFXMaterialFlags(Enum):
	NULL = 0 # No material effect
	BUMPMAP = 1 # Bump mapping 
	ENVMAP = 2 # Environment mapping 
	BUMPENVMAP = 3 # Bump and environment mapping 
	DUAL = 4 # Dual pass 
	UVTRANSFORM = 5 # Base UV transform 
	DUALUVTRANSFORM = 6 # Dual UV transform (2 pass)


# -------------------------------------------------------------------------------------------------
class TextureAttrbutes(IntEnum):
	LUM8A8 = 0
	NATIVE = 4 # Use for most GC
	C1555 = 0x0100
	C565 = 0x0200
	C4444 = 0x0300
	LUM8 = 0x0400
	C8888 = 0x0500
	C888 = 0x0600
	D16 = 0x0700 # A 16-bit texture format used for depth buffer purposes.
	D24 = 0x0800 # A 24-bit texture format used for depth buffer purposes.
	D32 = 0x0900 # A 32-bit texture format used for depth buffer purposes.
	C555 = 0x0A00
	AUTOMIPMAPS = 0x1000 # A flag indicating that the texture uses automatic mipmap generation.
	PAL8 = 0x2000 # A palette texture format with 256 colors.
	PAL4 = 0x4000 # A palette texture format with 16 colors.
	MIPMAPS = 0x8000 # A flag indicating that the texture uses mipmapping.
	UNK = 0x20000


# -------------------------------------------------------------------------------------------------
class TexturePlatform(Enum):
	XBOX = 5
	D3D8 = 8
	D3D9 = 9
	GC = 0x6000000 # 6 in BigEndian
	PS2 = 0x325350 # PS2 as string
	PSP = 0x505350 # PSP as string


# -------------------------------------------------------------------------------------------------
def process_chunk(br, parent=None):

	chunk = Chunk().read(br, parent)

	#print('reading chunk', chunk.get_type())

	# handle struct chunks and de-serialize them
	if chunk.get_type() == ChunkType.STRUCT:
		chunk.raw = br.read_bytes(chunk.get_size())
		deserialize_chunk_struct(chunk)

	# handle strings separately... @todo: unicode strings
	elif chunk.get_type() == ChunkType.STRING:
		chunk.string = br.read_bytes(chunk.get_size())

	# handle nested chunks
	elif chunk.is_container():
		if chunk.get_size() == 0:
			print(f'Skipping empty chunk {chunk.get_type()}')
			return chunk
		while (br.stream.tell() < chunk.get_start() + chunk.get_size()):
			tmp = process_chunk(br, parent=chunk)
			chunk.chunks.append(tmp)

	# handle remaining chunks... @todo: de-serialize
	else:
		# ----------------------------------------
		if chunk.get_size() > 12:
			br.seek(8, os.SEEK_CUR)
			tmp_version = br.read_uint32()
			#assert tmp_version != 0x00000310
			if tmp_version == 0x00000310:
				raise NotImplementedError(f'Unhandled container Chunk {chunk.get_type()}')
			br.seek(-12, os.SEEK_CUR)
		# ----------------------------------------
		chunk.raw = br.read_bytes(chunk.get_size())
		deserialize_chunk_data(chunk)

	return chunk


# -------------------------------------------------------------------------------------------------
def deserialize_chunk_data(chunk):
	parser = BinaryReader(chunk.raw)
	if chunk.get_type() == ChunkType.BINMESHPLUGIN:
		chunk.data = BinMeshData(parser)
	elif chunk.get_type() == ChunkType.COLLISPLUGIN:
		chunk.data = CollisionData(parser)
	elif chunk.get_type() == ChunkType.MATERIALEFFECTSPLUGIN:
		chunk.data = MaterialEffectsData(parser)
	elif chunk.get_type() == ChunkType.EXTENSIONTHPS:
		parent = chunk.get_parent()
		if parent.get_parent() is not None:
			if parent.get_parent().get_type() == ChunkType.ATOMICSECT:
				chunk.data = AtomicSectionExtensionData(parser, parent)
			elif parent.get_parent().get_type() == ChunkType.MATERIAL:
				chunk.data = MaterialExtensionData(parser, parent)
			elif parent.get_parent().get_type() == ChunkType.TEXTURE:
				chunk.data = TextureExtensionData(parser, parent)
			elif parent.get_parent().get_type() == ChunkType.ATOMIC:
				chunk.data = AtomicExtensionData(parser, parent)
			else:
				print(f'Got THPS3 Extension but parent type is {parent.get_parent().get_type()}...')
				pass
		else:
			# root extension probably
			print(f'Got THPS3 Extension but parent is an orphan {parent.get_type()}...?')
			pass
	else:
		#raise NotImplementedError(f'Unhandled Data for {chunk.get_type()}')
		print(f'Skip parsing data for {chunk.get_type()} with size {chunk.get_size()} at {chunk.get_start()}...')


# -------------------------------------------------------------------------------------------------
def deserialize_chunk_struct(chunk):
	parser = BinaryReader(chunk.raw)
	if chunk.get_parent().get_type() == ChunkType.WORLD:
		chunk.struct = WorldStruct(parser)
	elif chunk.get_parent().get_type() == ChunkType.MATLIST:
		chunk.struct = MaterialListStruct(parser)
	elif chunk.get_parent().get_type() == ChunkType.MATERIAL:
		chunk.struct = MaterialStruct(parser)
	elif chunk.get_parent().get_type() == ChunkType.TEXTURENATIVE:
		chunk.struct = TextureNativeStruct(parser)
	elif chunk.get_parent().get_type() == ChunkType.ATOMIC:
		chunk.struct = AtomicStruct(parser)
	elif chunk.get_parent().get_type() == ChunkType.GEOMETRYLIST:
		chunk.struct = GeometryListStruct(parser)
	elif chunk.get_parent().get_type() == ChunkType.GEOMETRY:
		chunk.struct = GeometryStruct(parser)
	elif chunk.get_parent().get_type() == ChunkType.TEXTURE:
		chunk.struct = TextureStruct(parser)
	elif chunk.get_parent().get_type() == ChunkType.ATOMICSECT:
		chunk.struct = AtomicSectionStruct(parser, chunk)
	elif chunk.get_parent().get_type() == ChunkType.CLUMP:
		chunk.struct = ClumpStruct(parser)
	elif chunk.get_parent().get_type() == ChunkType.FRAMELIST:
		chunk.struct = FrameListStruct(parser)
	elif chunk.get_parent().get_type() == ChunkType.PLANESECT:
		# ehh, we just discard this later anyways...
		# as we're only interested in the atomic sections 
		pass
	else:
		#raise NotImplementedError(f'Unhandled Struct for {parent.get_type()}')
		print(f'Skip parsing struct for {chunk.get_parent().get_type()} with size {chunk.get_size()} at {chunk.get_start()}...')


# -------------------------------------------------------------------------------------------------
class Struct(object):
	def toJSON(self):
		result = {}
		for attr, value in self.__dict__.items():
			result[attr] = value
		return result


# -------------------------------------------------------------------------------------------------
class BinMeshData(Struct):
	def __init__(self, br):
		super().__init__()
		self.face_type = br.read_uint32()
		self.num_splits = br.read_uint32()
		self.total_num_indices = br.read_uint32()
		self.splits = []
		for _ in range(self.num_splits):
			split = {}
			split['num_indices'] = br.read_uint32()
			split['material_index'] = br.read_uint32()
			split['indices'] = [br.read_uint32() for _ in range(split['num_indices'])]
			self.splits.append(split)


# -------------------------------------------------------------------------------------------------
class CollisionData(Struct):

	def __init__(self, br):
		super().__init__()
		pass


# -------------------------------------------------------------------------------------------------
class MaterialEffectsData(Struct):

	def __init__(self, br):
		super().__init__()
		pass


# -------------------------------------------------------------------------------------------------
class AtomicSectionExtensionData(Struct):

	# @note: maybe pass the chunk instead, and get the parent from that?
	def __init__(self, br, parent):
		super().__init__()
		assert parent.get_type() == ChunkType.EXTENSION
		assert parent.get_parent().get_type() == ChunkType.ATOMICSECT
		assert parent.get_parent().get_child_struct() is not None
		num_triangles = parent.get_parent().get_child_struct().num_triangles
		self.padding = br.read_uint32() # @todo: idk always 6??
		assert self.padding == 6
		self.flags = [br.read_uint16() for _ in range(num_triangles)]
		self.unkXX = br.read_uint32() # @todo
		#assert self.unkXX == 0
		self.name = br.read_uint32() # sector checksum name
		self._name = str(tohex(self.name, 32))
		br.seek(self.padding, os.SEEK_CUR) # padding?


# -------------------------------------------------------------------------------------------------
class AtomicExtensionData(Struct):

	# @note: maybe pass the chunk instead, and get the parent from that?
	def __init__(self, br, parent):
		super().__init__()
		pass # @todo


# -------------------------------------------------------------------------------------------------
class MaterialExtensionData(Struct):

	# @note: maybe pass the chunk instead, and get the parent from that?
	def __init__(self, br, parent):
		super().__init__()
		assert parent.get_type() == ChunkType.EXTENSION
		assert parent.get_parent().get_type() == ChunkType.MATERIAL
		assert parent.get_parent().get_child_struct() is not None
		pass # @todo


# -------------------------------------------------------------------------------------------------
class TextureExtensionData(Struct):

	# @note: maybe pass the chunk instead, and get the parent from that?
	def __init__(self, br, parent):
		super().__init__()
		assert parent.get_type() == ChunkType.EXTENSION
		assert parent.get_parent().get_type() == ChunkType.TEXTURE
		assert parent.get_parent().get_child_struct() is not None
		pass # @todo


# -------------------------------------------------------------------------------------------------
class FrameListStruct(Struct):
	def __init__(self, br):
		super().__init__()
		self.num_frames = br.read_uint32()
		self.frames = []
		for _ in range(self.num_frames):
			frame = {}
			frame['right'] = br.read_vec3()
			frame['up'] = br.read_vec3()
			frame['forward'] = br.read_vec3()
			frame['position'] = br.read_vec3()
			frame['parent_frame'] = br.read_int32()
			frame['unknown'] = br.read_uint32()
			self.frames.append(frame)


# -------------------------------------------------------------------------------------------------
class ClumpStruct(Struct):
	def __init__(self, br):
		super().__init__()
		self.num_atomics = br.read_uint32()
	#	self.num_lights = br.read_uint32()
	#	self.num_cameras = br.read_uint32()


# -------------------------------------------------------------------------------------------------
class WorldStruct(Struct):
	def __init__(self, br):
		super().__init__()
		self.root_is_world_sector = br.read_int32()
		self.inverse_origin = br.read_vec3()
		self.ambient = br.read_float()
		self.specular = br.read_float()
		self.diffuse = br.read_float()
		self.num_triangles = br.read_uint32()
		self.num_vertices = br.read_uint32()
		self.num_planes = br.read_uint32()
		self.num_atomics = br.read_uint32()
		self.collision_sector_size = br.read_uint32()
		self.flags = br.read_uint32()


# -------------------------------------------------------------------------------------------------
class MaterialListStruct(Struct):
	def __init__(self, br):
		super().__init__()
		self.num_materials = br.read_uint32()
		#assert self.num_materials == 255 # @testing, ap.bsp
		# skipping the material instance stuff
		br.seek(self.num_materials * 4, os.SEEK_CUR)


# -------------------------------------------------------------------------------------------------
class TextureNativeStruct(Struct):
	def __init__(self, br):
		super().__init__()
		self.platform = TexturePlatform(br.read_uint32())
		# @todo
		self.size = br.read_uint32() # maybe
		self.name = br.read_bytes(128).decode('utf-8', 'ignore').split('\x00', 1)[0] # eh
		self.alpha = br.read_bytes(128).decode('utf-8', 'ignore').split('\x00', 1)[0] # eh
		self.flags = br.read_uint32()
		if (self.flags & TextureAttrbutes.MIPMAPS):
			print('has mipmaps!')
		if (self.flags & TextureAttrbutes.AUTOMIPMAPS):
			print('has auto mipmaps!')
		# @todo


# -------------------------------------------------------------------------------------------------
class MaterialStruct(Struct):
	def __init__(self, br):
		super().__init__()
		self.flags = br.read_uint32()
		self.color = br.read_uint32()
		self.unk08 = br.read_uint32()
		self.has_texture = br.read_uint32()
		self.ambient = br.read_float()
		self.specular = br.read_float()
		self.diffuse = br.read_float()


# -------------------------------------------------------------------------------------------------
class GeometryListStruct(Struct):
	def __init__(self, br):
		super().__init__()
		self.num_geom = br.read_uint32()


# -------------------------------------------------------------------------------------------------
class GeometryStruct(Struct):
	def __init__(self, br):
		super().__init__()
		self.flags = br.read_uint16()
		br.seek(2, os.SEEK_CUR) # hmm
		self.num_triangles = br.read_uint32()
		self.num_vertices = br.read_uint32()
		self.num_frames = br.read_uint32()
		br.seek(12, os.SEEK_CUR) # @todo light stuff?

		if (self.flags & GeometryFlags.NATIVE):
			raise NotImplementedError('NATIVE GEOMETRY STUFF!!!')
		if (self.flags & GeometryFlags.PRELIT):
			self.colors = [br.read_uint32() for _ in range(self.num_vertices)]
		if (self.flags & GeometryFlags.TEXTURED):
			self.uvs = [br.read_vec2() for _ in range(self.num_vertices)]
		if (self.flags & GeometryFlags.TEXTURED2):
			self.uvs2 = [br.read_vec2() for _ in range(self.num_vertices)]

		def read_triangles(br, count):
			triangles = []
			for _ in range(count):
				triangles.append(br.read_uint16())
				triangles.append(br.read_uint16())
				br.seek(2, os.SEEK_CUR) # hmm
				triangles.append(br.read_uint16())
			return triangles

		self.triangles = read_triangles(br, self.num_triangles)
		self.vertices = [br.read_vec3() for _ in range(self.num_vertices)]
	
		if (self.flags & GeometryFlags.NORMALS):
			self.normals = [br.read_vec3() for _ in range(self.num_vertices)]

		# @todo??


# -------------------------------------------------------------------------------------------------
class AtomicStruct(Struct):
	def __init__(self, br):
		super().__init__()
		self.frame_index = br.read_uint32()
		self.geometry_index = br.read_uint32()
		self.flags = br.read_uint32()
		br.seek(4, os.SEEK_CUR) # padding?


# -------------------------------------------------------------------------------------------------
class TextureStruct(Struct):
	def __init__(self, br):
		super().__init__()
		# @note: will contain texture flags, but if texture is in tdx those flags are overriden by tdx texflags - vadru
		self.flags = br.read_uint32()


# -------------------------------------------------------------------------------------------------
class AtomicSectionStruct(Struct):
	def __init__(self, br, chunk):
		super().__init__()
		self.unk00 = br.read_uint32() # @todo, material list window base?
		self.num_triangles = br.read_uint32()
		self.num_vertices = br.read_uint32()
		self.bbox = [br.read_float() for _ in range(6)]
		br.seek(4, os.SEEK_CUR) # possibly collision sector flag?
		br.seek(4, os.SEEK_CUR) # unused?
		self.vertices = [br.read_vec3() for _ in range(self.num_vertices)]
		world = chunk.get_root().get_child_struct()
		if (world.flags & GeometryFlags.NORMALS):
			br.seek(self.num_vertices * 4, os.SEEK_CUR)
		self.colors = [br.read_uint32() for _ in range(self.num_vertices)]
		self.uvs = [br.read_vec2() for _ in range(self.num_vertices)]
		if any([
			(world.flags & GeometryFlags.MODULATEMATERIALCOLOR),
			(world.flags & GeometryFlags.TEXTURED2)
		]):
			br.seek(self.num_vertices * 8, os.SEEK_CUR)
		# @todo
		# self.collision = [[br.read_uint16() for _ in range(4)] for _ in range(self.num_triangles)]


# -------------------------------------------------------------------------------------------------
class Chunk(object):

	raw = None
	data = None
	struct = None
	string = None

	# @todo, generalize data and struct... move string to String chunk?

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
		elif self.type == ChunkType.STRUCT:
			if self.struct is not None:
				result['struct'] = self.struct.toJSON()
		elif self.type == ChunkType.STRING:
			result['string'] = str(self.string)
		elif self.data is not None:
			result['data'] = self.data.toJSON()
		if self.raw is not None:
			result['raw'] = self.raw.hex()
		result['offset'] = str(tohex(self.get_start(), 32))

		return result

	# whether this chunk contains other chunks
	def is_container(self):
		return (self.type in [
			# ----- common -----
			ChunkType.EXTENSION,
			ChunkType.MATLIST,
			ChunkType.MATERIAL,
			ChunkType.TEXTURE,
			# ----- tdx -----
			ChunkType.TEXDICTIONARY, 
			ChunkType.TEXTURENATIVE, 
			# ----- bsp ----- 
			ChunkType.WORLD,
			ChunkType.PLANESECT,
			ChunkType.ATOMICSECT,
			# ----- dff -----
			ChunkType.CLUMP,
			ChunkType.FRAMELIST,
			ChunkType.GEOMETRYLIST,
			ChunkType.GEOMETRY,
			ChunkType.ATOMIC,
		])

	# 
	def get_child_struct(self):
		if len(self.chunks) > 0:
			return find_first_chunk_with_type(self.chunks, ChunkType.STRUCT).struct
		return None

	# 
	def get_root(self):
		current = self
		while current.parent:
			current = current.parent
		return current

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

	def flatten_binary_tree(root, target_type):

		if root.get_type() == target_type:
			return [root]

		result = []
		for chunk in root.chunks:
			result.extend(flatten_binary_tree(chunk, target_type))

		return result

	# -- flatten plane sections
	plane = find_first_chunk_with_type(root.chunks, ChunkType.PLANESECT)
	assert plane.get_type() == ChunkType.PLANESECT
	atomics = flatten_binary_tree(plane, ChunkType.ATOMICSECT)
	root.chunks.remove(plane)
	root.chunks.extend(atomics)

	# -- debug
	with open('./tests/data/ap.json', 'w') as out:
		json.dump(root.toJSON(), out, indent=4)

	# -- debug
	#with open('./tests/data/ap-atomics.json', 'w') as out:
	#	json.dump([chunk.toJSON() for chunk in atomics], out, indent=4)

	def handle_materials(root):
		container = find_first_chunk_with_type(root.chunks, ChunkType.MATLIST)
		materials = find_chunks_with_type(container.chunks, ChunkType.MATERIAL)
	#	print(container)
	#	print(materials)

	def handle_objects(root):
		pass

	handle_materials(root)
	handle_objects(root)


# -------------------------------------------------------------------------------------------------
sys.setrecursionlimit(2048 * 2)


# -------------------------------------------------------------------------------------------------
def Chunky(filename):

	pathname = Path(filename).resolve()
	extension = pathname.suffix.lower().strip('.')
	scenename = pathname.stem.lower()
	with open(pathname, 'rb') as inp:

		# create an an instance of our reader class
		br = BinaryReader(inp)

		# go to the end of the stream to get the total file size
		br.stream.seek(0, os.SEEK_END)
		filesize = br.stream.tell()
		br.stream.seek(0, os.SEEK_SET)

		print('filesize', filesize)

		# separate tests for bsp files
		if extension == 'bsp':
			root = process_chunk(br, None)
			assert root.get_type() == ChunkType.WORLD
			to_scene(root, 'ap.scn.xbx')
			return root

		# separate tests for dff files
		elif extension == 'dff':
			chunks = []
			while (br.stream.tell() < filesize):
				chunks.append(process_chunk(br, None))
			assert chunks[0].get_type() == ChunkType.CLUMP

			# -- debug
			with open(f'./tests/data/{scenename}-dff.json', 'w') as out:
				json.dump([chunk.toJSON() for chunk in chunks], out, indent=4)
			return chunks

		# separate tests for skn files
		elif extension == 'skn':
			root = process_chunk(br, None)
			with open(f'./tests/data/{scenename}-skn.json', 'w') as out:
				json.dump(root.toJSON(), out, indent=4)
			return root

		# separate tests for tdx files
		elif extension == 'tdx':
			root = process_chunk(br, None)
			with open(f'./tests/data/{scenename}-tdx.json', 'w') as out:
				json.dump(root.toJSON(), out, indent=4, default=str)
			return root

		return None
