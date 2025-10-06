# example tools
Here are some example tools using the `thps-formats` library. These are mainly replacement tools for the new THUG Pro build/toolchain.

## prerequisites
- [uv](https://github.com/astral-sh/uv)

## building

```shell
# build a single tool
cd qcompy
sh build.sh

# or build all tools at once
cd examples
sh build-all.sh
```

## tools
- qcompy – qb script compiler
- prepack – asset packaging tool with lzss compression
- fontgen – font file generator from bmfnt files
- asscopy – asset file copier
- runmenow – hot-reload qb scripts into running game process
