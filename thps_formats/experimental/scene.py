# scene>sector>split

# maybe use this library?
# - https://github.com/niftools/pyffi/blob/develop/pyffi/utils/trianglestripifier.py

# generic format:
# - sector contains all vertices in arrays
# - triangles stored per split/mesh
# - unknown
# 	- lod levels???
# 	- multiple vertex buffers??? for effects only?

# thps3 notes:
# - sector vertices shared for render and collision

# thug1/thps4 notes:
# - sector contains all vertices in arrays
# - triangle strips stored per split/mesh

# thug2 notes:
# - interleaved vertices per split/mesh
# - triangle strips stored per split/mesh
# - mutliple vertex buffers per split/mesh

# blender collision notes:
# - does not handle double sided triangles
# 	- same three vertices cannot be shared by multiple triangles
# 		- ie. two triangles with different winding order...
# 		- solution: duplicate the vertices? special flag?
# 	- discarded on import...
# 	- maybe detect double sided triangles when making generic scene
# 	- ensure that there are no double sided triangles with different face flags

# tests/assumptions:
# - ensure that there are no double sided triangles with different face flags 
# - ensure that render and collision vertices can be consolidated
# 	- normals? colors? intensity?
# 	- floating point precision?
# - check the differences between multiple vertex buffer
# 	- possibly only colors are different?
