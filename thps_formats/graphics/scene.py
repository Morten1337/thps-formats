import os
from enum import Enum, IntEnum
from pathlib import Path
from thps_formats.utils.reader import BinaryReader
from thps_formats.shared.enums import GameType
from thps_formats.scripting2.crc32 import crc32_generate

# -------------------------------------------------------------------------------------------------
# scene is a container for level data and geometry
# - unify `col` and `scn` objects

# native scene -> unified scene -> ...  

# --- notes ---------------------------------------------------------------------------------------
# - lod levels is never more than one - (tested thug2 only)
# - lod levels always have the same number of indices - (tested thug2 only)
#   - but they can be different indices... hmm - (tested thug2 only)
# - vertex buffers count is never more than two - (tested thug2 only)
# - vertex buffers all contain the same data - (tested thug2 only)


# -------------------------------------------------------------------------------------------------
class FilteringMode(Enum):
    NEAREST = 0
    LINEAR = 1
    NEAREST_MIPMAP_NEAREST = 2
    NEAREST_MIPMAP_LINEAR = 3
    LINEAR_MIPMAP_NEAREST = 4
    LINEAR_MIPMAP_LINEAR = 5


# -------------------------------------------------------------------------------------------------
class MaterialFlags(IntEnum):
    UV_WIBBLE = (1 << 0)
    VC_WIBBLE = (1 << 1)
    TEXTURED = (1 << 2)
    ENVIRONMENT = (1 << 3)
    DECAL = (1 << 4)
    SMOOTH = (1 << 5)
    TRANSPARENT = (1 << 6)
    PASS_COLOR_LOCKED = (1 << 7)
    SPECULAR = (1 << 8) # Specular lighting is enabled on this material (Pass0).
    BUMP_SIGNED_TEXTURE = (1 << 9) # This pass uses an offset texture which needs to be treated as signed data.
    BUMP_LOAD_MATRIX = (1 << 10) # This pass requires the bump mapping matrix elements to be set up.
    ANIMATED_TEX = (1 << 11) # This pass has a texture which animates.
    IGNORE_VERTEX_ALPHA = (1 << 12) # This pass should not have the texel alpha modulated by the vertex alpha.
    EXPLICIT_UV_WIBBLE = (1 << 14) # Uses explicit uv wibble (set via script) rather than calculated.
    WATER_EFFECT = (1 << 27) # This material should be processed to provide the water effect.
    NO_MAT_COL_MOD = (1 << 28)  # No material color modulation required (all passes have m.rgb = 0.5).


# -------------------------------------------------------------------------------------------------
class ObjectFlags(IntEnum):
    TEXTURED = 0x00000001
    COLORED = 0x00000002
    NORMALS = 0x00000004
    INVISIBLE = 0x00000008  
    SKINNED = 0x00000010
    DYNAMIC = 0x00000020
    OCCLUDER = 0x00000040
    HASCASREMOVEFLAGS = 0x00000080
    PASS_BIT_1 = 0x00000100
    PASS_BIT_2 = 0x00000200
    NO_SHADOW = 0x00000400
    VCWIBBLE = 0x00000800
    RENDER_SEPARATE = 0x00001000 # Def'd in SceneConv
    HASKBIAS = 0x00002000   
    NO_SHADOW_WALL = 0x00004000 # From SceneConv
    HASLODINFO = 0x00008000 # True if LOD info fields are included  aml
    SKELETALMODEL = 0x00010000 # Model that contains skeletal info for procedural animation  aml  (Only valid in model export)
    UNLIT = 0x00020000
    COLOR_LOCKED = 0x00040000
    GRASS = 0x00080000
    HASINTLODINFO = 0x00100000 # True if this object contains its LOD data internally
    SHADOWVOLUME = 0x00200000 # True if the object is flagged in PE as a shadow volume
    HAS4WEIGHTS = 0x00400000 # Skinned model uses 4 weights per vert
    BILLBOARD = 0x00800000  
    SS_NORMALS = 0x01000000 # Has normals solely for the purpose of determining which side should be rendered in a single-sided mesh
    PASS_BIT_3 = 0x02000000 # Extra pass bits for z-push (SceneConv only)
    PASS_BIT_4 = 0x04000000 # (SceneConv only)
    WATER = 0x08000000 # is a water material (SceneConv only)
    ABSENTINNETGAMES = 0x10000000 # Flaged if the object has AbsentInNetGames checked
    HASLODDISTS = 0x20000000 # Object contains distances used
    HASVERSIONINFO = 0x80000000 # Version info wasn't saved in original,  if included load version field

    # ---------------------------------------------------------------------------------------------
    @classmethod
    def get_set_flags(cls, flags_value):
        return [flag.name for flag in cls if flags_value & flag]


# -------------------------------------------------------------------------------------------------
class SceneMaterial:

    # ---------------------------------------------------------------------------------------------
    def __init__(self):

        self.passes = []

        # @todo: set sane defaults 

        self.water_enabled = False

        self.grass_enabled = False
        self.grass_height = 0
        self.grass_layers = 0

        self.specular_power = 0.0
        self.specular_color = (1.0,1.0,1.0)

    # ---------------------------------------------------------------------------------------------
    @classmethod
    def from_reader(cls, br, game):
        material = cls()

        # material checksum
        material.checksum = br.read_uint32()

        # material name checksum ... eh
        if game >= GameType.THUG1:
            material.checksum2 = br.read_uint32()
        else:
            material.checksum2 = material.checksum

        material.num_passes = br.read_uint32()

        material.alpha_cuttof = br.read_int32()
        material.sorted = br.read_bool()
        material.draw_order = br.read_float()
        material.one_sided = br.read_bool()

        if game >= GameType.THUG1:
            material.two_sided = br.read_bool()
            material.base_pass = br.read_int32()
        else:
            material.two_sided = (not material.one_sided) # True?
            material.base_pass = 1

        material.grass_enabled = br.read_bool()
        if material.grass_enabled:
            material.grass_height = br.read_float()
            material.grass_layers = br.read_int32()

        if game >= GameType.THUG1:
            material.specular_power = br.read_float()
            if material.specular_power > 0:
                material.specular_color[0] = br.read_float()
                material.specular_color[1] = br.read_float()
                material.specular_color[2] = br.read_float()

        for i in range(material.num_passes):
            # @todo: handle texture passes
            p = {
                'color': [0.5, 0.5, 0.5, 0.5], # eh
                'address_mode': [0, 0], # eh
                'env_tile': [3.0, 3.0], # eh
                'filtering_mode': [FilteringMode.LINEAR_MIPMAP_NEAREST, FilteringMode.LINEAR],
            }

            p['texture'] = br.read_uint32()
            p['flags'] = br.read_uint32()

            p['color_enabled'] = br.read_bool()
            p['color'][0] = br.read_float()
            p['color'][1] = br.read_float()
            p['color'][2] = br.read_float()

            p['blend_mode'] = br.read_uint32()
            p['fixed_alpha'] = br.read_int32()

            p['address_mode'][0] = br.read_int32()
            p['address_mode'][1] = br.read_int32()

            if game >= GameType.THUG1:
                p['env_tile'][0] = br.read_float()
                p['env_tile'][1] = br.read_float()

            p['filtering_mode'][0] = FilteringMode(br.read_int16())
            p['filtering_mode'][1] = FilteringMode(br.read_int16())

            if game < GameType.THUG1:
                br.seek(12, os.SEEK_CUR) # diffuse rgb
                material.specular_color[0] = br.read_float()
                material.specular_color[1] = br.read_float()
                material.specular_color[2] = br.read_float()
                if sum(material.specular_color) > 0:
                    material.specular_power = 1.0
                else:
                    material.specular_power = 0.0
                br.seek(12, os.SEEK_CUR) # ambient rgb

            if (p['flags'] & MaterialFlags.UV_WIBBLE):
                p['fx_uv_uvel'] = br.read_float()
                p['fx_uv_vvel'] = br.read_float()
                p['fx_uv_ufreq'] = br.read_float()
                p['fx_uv_vfreq'] = br.read_float()
                p['fx_uv_uamp'] = br.read_float()
                p['fx_uv_vamp'] = br.read_float()
                p['fx_uv_uphase'] = br.read_float()
                p['fx_uv_vphase'] = br.read_float()

            first_pass = (i == 0)
            if first_pass and (p['flags'] & MaterialFlags.VC_WIBBLE):
                p['fx_vc_num_seq'] = br.read_uint32()
                for seq in range(p['fx_vc_num_seq']):
                    num_frames = br.read_uint32()
                    phase = br.read_uint32()
                    br.seek(num_frames * 8, os.SEEK_CUR) # sizeof(time + rgba)

            if (p['flags'] & MaterialFlags.ANIMATED_TEX):
                num_keyframes = br.read_int32()
                period = br.read_int32()
                iterations = br.read_int32()
                phase = br.read_int32()
                br.seek(num_keyframes * 8, os.SEEK_CUR) # sizeof(time + texture)
            
            br.seek(8, os.SEEK_CUR) # mag and min filtering mode
            br.seek(8, os.SEEK_CUR) # k and l mipmap

            material.passes.append(p)

        return material


# -------------------------------------------------------------------------------------------------
class SceneObject:

    # ---------------------------------------------------------------------------------------------
    def __init__(self):
        self.meshes = []

    # ---------------------------------------------------------------------------------------------
    @classmethod
    def from_reader(cls, br, game):
        obj = cls()
        obj.checksum = br.read_uint32()
        obj.transform_index = br.read_int32()
        obj.flags = br.read_uint32()
        obj.num_meshes = br.read_uint32()

        br.seek(24, os.SEEK_CUR) # @todo: bounding box
        br.seek(16, os.SEEK_CUR) # @todo: bounding sphere

        # print(ObjectFlags.get_set_flags(obj.flags))

        if obj.flags & ObjectFlags.BILLBOARD:
            br.seek(40, os.SEEK_CUR) # @todo: billboard

        if game == GameType.DESA:
            br.seek(8, os.SEEK_CUR) # @todo: unknown

        if game < GameType.THUG2:
            raise NotImplementedError('Loading THPS4/THUG1 objects not supported yet')

        for i in range(obj.num_meshes):
            mesh = SceneMesh.from_reader(br, obj, game)
            obj.meshes.append(mesh)

        return obj


# -------------------------------------------------------------------------------------------------
class SceneMesh:

    # ---------------------------------------------------------------------------------------------
    def __init__(self):
        self.vertex_buffers = []
        self.num_lod_levels = 1
        self.faces = [] # @todo: lod levels
        self.lods = [] # @todo: lod levels
        self.lod_level_distances = []
        self.vertex_shaders = [-1, -1]

    # ---------------------------------------------------------------------------------------------
    @classmethod
    def from_reader(cls, br, obj, game):
        mesh = cls()

        if game == GameType.MG: # monster garage xbox
            br.read_uint32() # same as obj.checksum

        if game >= GameType.THUG1:
            br.seek(16, os.SEEK_CUR) # @todo: bounding sphere
            br.seek(24, os.SEEK_CUR) # @todo: bounding box

        mesh.flags = br.read_uint32()
        mesh.material = br.read_uint32()

        if game >= GameType.THUG1:
            mesh.num_lod_levels = br.read_uint32()

        if game < GameType.THUG2:
            raise NotImplementedError('Loading THPS4/THUG1 meshes not supported yet')

        if obj.flags & ObjectFlags.HASINTLODINFO:
            print('HASINTLODINFO!')
        # print('num_lod_levels', mesh.num_lod_levels)
        assert mesh.num_lod_levels == 1
        for i in range(mesh.num_lod_levels):
            # @todo: handle this properly 
            lod_num_indices = br.read_uint32()
            mesh.lods = [br.read_uint16() for _ in range(lod_num_indices)] #
            tmp_num_indices = br.read_uint16()
            mesh.faces = [br.read_uint16() for _ in range(tmp_num_indices)]
            assert tmp_num_indices == lod_num_indices
            # if mesh.lods != mesh.faces:
            #     print('mesh has different lod face indices')
            # if mesh.lods != mesh.faces:
            #     print('---------------------------------------------------')
            #     print(mesh.lods)
            #     print(mesh.faces)
            # else:
            #     print('---- EQUAL FACE INDICES !! ------------------------')
            #     print(mesh.lods)
            #     print(mesh.faces)

        br.seek(14, os.SEEK_CUR) # padding
        mesh.stride = br.read_uint8()
        mesh.num_verts = br.read_uint16()
        mesh.num_buffers = br.read_uint16()
        
        assert mesh.num_buffers <= 2

        mesh.vertex_buffers = [[]] * mesh.num_buffers
        for i in range(mesh.num_buffers):
            if i > 0:
                br.seek(1, os.SEEK_CUR) # padding?
            buffer_size = br.read_uint32()
            for vi in range(mesh.num_verts):

                tmp_stride = 12
                mesh.vertex_buffers[i].extend(br.read_vec3())

                if obj.flags & ObjectFlags.SKINNED:
                    raise NotImplementedError('Loading skinned meshes not supported yet')

                if obj.flags & ObjectFlags.NORMALS:
                    tmp_stride += 12
                    mesh.vertex_buffers[i].extend(br.read_vec3())

                if obj.flags & ObjectFlags.COLORED:
                    tmp_stride += 4
                    mesh.vertex_buffers[i].extend([br.read_uint32()])

                tmp_num_texcoords = int((mesh.stride - tmp_stride) / 8)
                if obj.flags & ObjectFlags.TEXTURED:
                    tmp_stride += 8 * tmp_num_texcoords
                    for t in range(tmp_num_texcoords):
                        mesh.vertex_buffers[i].extend(br.read_vec2())

                assert (mesh.stride - tmp_stride) == 0
                # br.seek(mesh.stride - tmp_stride, os.SEEK_CUR) # @todo
            # br.seek(buffer_size, os.SEEK_CUR) # @todo
        if mesh.num_buffers > 1:
            assert mesh.vertex_buffers[0] == mesh.vertex_buffers[1]
            # print('---- EQUAL VERTEX POSITIONS -----------------------')
            # print(mesh.vertex_buffers[0])
            # print(mesh.vertex_buffers[1])

        mesh.vertex_shaders[0] = br.read_uint32()
        mesh.vertex_shaders[1] = br.read_uint32()
        mesh.normal_offset = br.read_uint8()
        mesh.color_offset = br.read_uint8()
        mesh.texcoord_offset = br.read_uint8()
        mesh.has_vc_wibble = br.read_bool()

        if mesh.has_vc_wibble:
            br.seek(mesh.num_verts, os.SEEK_CUR) # @todo

        num_lod_levels = br.read_uint32()
        if num_lod_levels > 1:
            mesh.lod_level_distances = [br.read_float() for _ in range(num_lod_levels)]

        mesh.pixel_shader = br.read_uint32()
        if mesh.pixel_shader == 1:
            mesh.pixel_shader_unknown = br.read_uint32()
            mesh.pixel_shader_size = br.read_uint32()
            br.seek(mesh.pixel_shader_size, os.SEEK_CUR) # @todo

        return mesh


# -------------------------------------------------------------------------------------------------
class Scene:

    # ---------------------------------------------------------------------------------------------
    def __init__(self):
        self.materials = []
        self.objects = []

    # ---------------------------------------------------------------------------------------------
    def load(self, filename):
        pathname = Path(filename).resolve()

        if not pathname.exists():
            raise FileNotFoundError(F"File does not exist... '{pathname}'")

        if '.scn' in pathname.suffixes or '.mdl' in pathname.suffixes:
            self.load_scn(pathname)
        elif '.col' in pathname.suffixes:
            raise NotImplementedError('Loading col files not supported yet...')
        elif '.q' in pathname.suffixes:
            raise NotImplementedError('Loading q files not supported yet...')
        else:
            raise NotImplementedError('In fact loading any files is not supported...')

    # ---------------------------------------------------------------------------------------------
    def load_scn(self, filename, game=GameType.THUG2):
        pathname = Path(filename).resolve()

        if not pathname.exists():
            raise FileNotFoundError(F"File does not exist... '{pathname}'")

        with open(pathname, 'rb') as inp:
            br = BinaryReader(inp)

            # @todo: handle version stuff
            br.seek(12, os.SEEK_SET)

            # handle materials
            num_materials = br.read_uint32()
            for i in range(num_materials):
                material = SceneMaterial.from_reader(br, game)
                self.materials.append(material)

            # handle sectors
            num_sectors = br.read_uint32()
            for i in range(num_sectors):
                # if i > 0:
                #     break
                obj = SceneObject.from_reader(br, game)
                self.objects.append(obj)

            if filename.stem.upper() == 'BA':
                assert self.objects[0].checksum == crc32_generate('BA_Wire03')
                assert self.objects[-1].checksum == crc32_generate('TS_BLDN_indoor')

    # ---------------------------------------------------------------------------------------------
    @classmethod
    def from_file(cls, filename):
        scene = cls()
        scene.load(filename)
        return scene

    # ---------------------------------------------------------------------------------------------
    @classmethod
    def from_files(cls, files):
        scene = cls()
        for f in files:
            scene.load(f)
        return scene
