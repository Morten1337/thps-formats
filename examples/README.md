# example tools
Here are some example tools using the `thps-formats` library. These are mainly replacement tools for the new THUG Pro build/toolchain. These should probably be moved to a separate repository anyway.

## building
The tools are packaged into executables with `pyinstaller`. There's a shared spec file so that the Python base library can be shared. Although it might be better to use other build options to package everything within the executable.

You should have a clean virtual environment with `pyinstaller` along with the packages required by the main library. Otherwise, there will be even more junk packaged into the executable. There's more to be desired here, but it works for now.

```shell
$ pyinstaller --clean --noconfirm build.spec
```

## note
There are a few hard-coded paths here and there. So if you want to build it yourself, you'll probably have to change that.
