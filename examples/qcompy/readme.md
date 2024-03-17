# qcompy

## description
a sample q compiler using the `thps_formats` library

## usage
```sh
$ qcompy filename.q
$ qcompy path/ --recursive --output output/
$ qcompy filename.q --defines DEVLOPER,FOO --debug
```

## build
install the base projects' requirements in a virtual environment,
then run the `build.bat` to package this app using `pyinstaller`
