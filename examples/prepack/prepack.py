import os
import sys
import argparse
import nlzss11
from pathlib import Path

#sys.path.insert(0, os.path.abspath('../../'))

from thps_formats.utils.writer import BinaryWriter
from thps_formats.utils.reader import BinaryReader
from thps_formats.scripting2.crc32 import crc32_generate


# ------------------------------------------------------------------------------
def get_relative_path(filepath, basepaths):
    for basepath in basepaths:
        try:
            index = filepath.parts.index(basepath.split('/')[-1])
            return Path(*filepath.parts[index + 1:])
        except ValueError:
            continue
    return None


# ------------------------------------------------------------------------------
def parse_build_file(inputpath):
    files = []
    with inputpath.open('r') as file:
        for line in file:
            cleaned_line = line.split(';')[0].strip()
            if not cleaned_line:
                continue
            filename = Path(cleaned_line).resolve()
            if not filename.is_file():
                raise Exception(F"Couldn't find the file with name! {filename}")
            files.append(filename)
    return files


# ------------------------------------------------------------------------------
def prepack(args):

    files = []

    if not args.input:
        raise Exception('No input file or directory specified!')

    if not args.output:
        raise Exception('No output file or directory specified!')

    inputpath = Path(args.input).resolve()
    if '.' in inputpath.name or inputpath.is_file():
        if not inputpath.exists():
            raise Exception('The input file does not exist!')
        files.extend(parse_build_file(inputpath))
    else:
        if not inputpath.exists():
            raise Exception('The input directory does not exist!')
        for inputfile in inputpath.rglob('*.*'):
            if inputfile.is_file():
                files.append(inputfile.resolve())

    outputpath = Path(args.output).resolve()
    if '.' in outputpath.name:
        outputfile = outputpath
    else:
        if not outputpath.exists():
            raise Exception('The output directory does not exist!')
        if inputpath.is_dir():
            raise Exception('Please specify a output file when input is a directory!')
        outputfile = (outputpath / inputpath.name).with_suffix('.prx')

    if args.debug:
        print(files)
        print(inputpath)
        print(outputfile)

    with open(outputfile, 'wb') as out:
        writer = BinaryWriter(out)
        writer.write_uint32(0x69696969) # pre file size placeholder 
        writer.write_uint32(0xabcd0003) # pre file version
        writer.write_uint32(len(files)) # number of files

        for file in files:
            print(F"[{outputfile.name}] adding file '{file}'")

            if args.thugpro:
                filepath = str(get_relative_path(file, ['source', 'output/data']))
            else:
                filepath = str(file.relative_to(Path.cwd()))

            paddedpath = filepath + '\x00'
            remainder = (4 - (len(paddedpath) % 4))
            if remainder != 4:
                paddedpath = paddedpath + '\x00' * remainder

            filesize = os.path.getsize(file)
            with open(file, 'rb') as inp:
                data = inp.read()
                if args.compress:
                    compesseddata = nlzss11.compress(data, level=7)
                    compessedsize = len(compesseddata)

                    if compessedsize < filesize:
                        writer.write_uint32(filesize)
                        writer.write_uint32(compessedsize)
                        writer.write_uint32(len(paddedpath))
                        writer.write_uint32(crc32_generate(filepath))
                        writer.write_string(paddedpath)
                        writer.write_bytes(compesseddata)
                    else:
                        writer.write_uint32(filesize)
                        writer.write_uint32(0)
                        writer.write_uint32(len(paddedpath))
                        writer.write_uint32(crc32_generate(filepath))
                        writer.write_string(paddedpath)
                        writer.write_bytes(data)
                else:
                    writer.write_uint32(filesize)
                    writer.write_uint32(0)
                    writer.write_uint32(len(paddedpath))
                    writer.write_uint32(crc32_generate(filepath))
                    writer.write_string(paddedpath)
                    writer.write_bytes(data)

            padding = (4 - (writer.stream.tell() % 4))
            if padding != 4:
                writer.write_bytes(b'\x00' * padding)

        totalsize = writer.stream.tell()
        writer.seek(0)
        writer.write_uint32(totalsize)


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='prepack is a tool for packing game assets!')
    parser.add_argument('input', metavar='package.txt [source/]', nargs='?', type=str, help='build file or directory')
    parser.add_argument('--output', metavar='package.prx [pre/]', type=str, help='output file name or directory')
    parser.add_argument('--compress', action='store_true', help='compress files with LZSS')
    parser.add_argument('--thugpro', action='store_true', help='deal with source/output relative paths in build files')
    parser.add_argument('--debug', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        prepack(args)
    except Exception as e:
        print(e)

# $ prepack build.txt --output path/pre/ --compress
# $ prepack source/ --output path/pre/package.prx --thugpro
