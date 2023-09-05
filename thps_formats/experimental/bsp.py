import os
from pathlib import Path as Path
from thps_formats.utils.reader import BinaryReader

# @note: just porting my old ugly c# code to python...
# the classes/objects are not really meant to fully represent the bsp data format...
# they're more of a intermediate way to store data before converting it to thps scene format.
# the bsp format is chunk-based, so there could probably just be a single recursive
# switch function to parse the whole file. but for some reason i did not do that originally.


class Scene(object):

	def __init__(self, scene):
		pass

	def to_file(self, filename, format):
		return False


class Material(object):

	def __init__(self, br, chunk):
		pass


class Chunk(object):

	def __init__(self, br):
		self.start = br.stream.tell()
		self.type = br.read_uint32()
		self.size = br.read_uint32()
		br.read_uint32()


class BSP(object):

	def __init__(self, filename):

		self.pathname = Path(filename).resolve()
		self.filename = self.pathname.name
		self.scenename = self.pathname.stem

		self.materials = []
		self.objects = []

		with open(self.pathname, 'rb') as inp:

			br = BinaryReader(inp)
			print()
			print('--------------------------------')
			print('pathname:', self.pathname)
			print('filename:', self.filename)
			print('scenename:', self.scenename)

			# go to the end of the stream to get the total file size
			br.stream.seek(0, os.SEEK_END)
			self.filesize = br.stream.tell()
			br.stream.seek(0, os.SEEK_SET)
			print('filesize:', self.filesize)

			print('--------------------------------')

			# @todo parse and check header
			br.read_bytes(72)

			self.world_flags = br.read_uint32()

			while (br.stream.tell() < self.filesize):
				chunk = Chunk(br)
				if chunk.type == 0x00000008: # Material Container
					self.process_materials_chunk(chunk, br)
				elif chunk.type == 0x00000009: # Atomic section - object
					pass
				elif chunk.type == 0x00000003: # extension
					pass
				elif chunk.type == 0x00000010: # clump
					br.stream.seek(chunk.size, os.SEEK_CUR)
				elif chunk.type == 0x0000000a: # dunno
					pass
				else:
					print('skipping unknown chunk at ', chunk.start)
					br.stream.seek(chunk.size, os.SEEK_CUR)
			
			# this should fail
			print(br.read_uint32())

	def process_material_chunk(self, chunk, br):
		# @note: this is as far as i got 
		return None

	def process_materials_chunk(self, chunk, br):
		# @todo parse this data?
		br.stream.seek(12, os.SEEK_CUR)
		num_materials = br.read_uint32()
		# @todo parse this data?
		br.stream.seek(4 * num_materials, os.SEEK_CUR)

		while (br.stream.tell() < chunk.start + chunk.size):
			material_chunk = Chunk(br)
			if material_chunk.type == 0x00000007: # Material
				material = self.process_material_chunk(material_chunk, br)
				if material:
					self.materials.push(material)
			else:
				print('skipping unknown material chunk at ', material_chunk.start)
				br.stream.seek(material_chunk.size, os.SEEK_CUR)

	def to_scene(self):
		return Scene(self)
