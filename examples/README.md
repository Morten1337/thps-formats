# example tools
Here are some example tools using the `thps-formats` library. These are mainly replacement tools for the new THUG Pro build/toolchain.

## prerequisites
- [uv](https://github.com/astral-sh/uv)

## building
Each tool can be built independently using its own `build.bat` script:

```shell
# build a single tool
cd qcompy
build.bat

# or build all tools at once
cd examples
build-all.bat
```

## tools
- qcompy – qb script compiler
- prepack – asset packaging tool with lzss compression
- fontgen – font file generator from bmfnt files
- asscopy – asset file copier
- runmenow – hot-reload qb scripts into running game process
