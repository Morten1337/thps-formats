import platform
from setuptools import setup, find_packages, Extension

# -------------------------------------------------------------------------------------------------
if platform.system() == 'Windows':
    extra_compile_args = ['/W0'] # msvc
else:
    extra_compile_args = ['-Wno-everything'] # clang/gcc

# -------------------------------------------------------------------------------------------------
ext_modules = [
    Extension(
        'thps_formats.encoding.lzss',
        sources=['thps_formats/encoding/pylzss.c'],
        include_dirs=['thps_formats/encoding/include'],
        extra_compile_args=extra_compile_args,
    )
]

# -------------------------------------------------------------------------------------------------
setup(
    name='thps_formats',
    version='0.1',
    packages=find_packages(),
    ext_modules=ext_modules,
)
