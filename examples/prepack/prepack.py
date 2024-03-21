import sys
import os
import argparse
import lzss
from pathlib import Path

from thps_formats.utils.writer import BinaryWriter
from thps_formats.scripting2.crc32 import crc32_generate


# ------------------------------------------------------------------------------
def get_relative_path(file_path, base_paths):
    for base_path in base_paths:
        try:
            index = file_path.parts.index(base_path.split('/')[-1])
            return Path(*file_path.parts[index + 1:])
        except ValueError:
            continue
    return None


# ------------------------------------------------------------------------------
def parse_build_file(input_file_path):
    files = []
    with input_file_path.open('r') as file:
        for line in file:
            cleaned_line = line.split(';')[0].strip()
            if not cleaned_line:
                continue
            file_name = Path(cleaned_line).resolve()
            if not file_name.is_file():
                raise Exception(F"Couldn't find the file with name! {file_name}")
            files.append(file_name)
    return files


# ------------------------------------------------------------------------------
def generate_container_file(output_file_path, package_files, args):

    with open(output_file_path, 'wb') as out:
        writer = BinaryWriter(out)
        writer.write_uint32(0x69696969) # pre file size placeholder 
        writer.write_uint32(0xabcd0003) # pre file version
        writer.write_uint32(len(package_files)) # number of files

        for file in package_files:

            print(F"[{output_file_path.name}] adding file '{file}'")

            if args.thugpro:
                file_path = str(get_relative_path(file, ['source', 'output/data']))
            else:
                file_path = str(file.relative_to(Path.cwd()))

            # ensure the path string is null-terminated and its length is a multiple of 4 bytes for alignment
            file_path_aligned = (file_path + '\x00')
            file_path_remainder = (4 - (len(file_path_aligned) % 4))
            if file_path_remainder != 4:
                file_path_aligned = (file_path_aligned + '\x00' * file_path_remainder)

            data_size = os.path.getsize(file)
            data_compressed_size = 0

            if args.compress:
                compressed_file_path = file.with_suffix(file.suffix + '_compressed')
                data_compressed_size = os.path.getsize(compressed_file_path)
                if data_compressed_size < data_size:
                    with open(compressed_file_path, 'rb') as inp:
                        data = inp.read()
                else:
                    data_compressed_size = 0
                    with open(file, 'rb') as inp:
                        data = inp.read()

            writer.write_uint32(data_size)
            writer.write_uint32(data_compressed_size)
            writer.write_uint32(len(file_path_aligned))
            writer.write_uint32(crc32_generate(file_path))
            writer.write_string(file_path_aligned)
            writer.write_bytes(data)

            # add zero padding to ensure the data size is a multiple of 4 bytes
            padding = (4 - (writer.stream.tell() % 4))
            if padding != 4:
                writer.write_bytes(b'\x00' * padding)

        file_size = writer.stream.tell()
        writer.seek(0)
        writer.write_uint32(file_size)


# ------------------------------------------------------------------------------
def prepack(args):

    package_files = []

    if not args.input:
        raise Exception('No input file or directory specified!')

    if not args.output:
        raise Exception('No output file or directory specified!')

    # check if the input argument is a file name (build txt file)
    input_file_path = Path(args.input).resolve()
    if '.' in input_file_path.name or input_file_path.is_file():
        if not input_file_path.exists():
            raise Exception('The input file does not exist!')
        package_files.extend(parse_build_file(input_file_path))
    else:
        # check if the input argument is a directory
        if not input_file_path.exists():
            raise Exception('The input directory does not exist!')
        for input_file_name in input_file_path.rglob('*.*'):
            if input_file_name.is_file():
                package_files.append(input_file_name.resolve())

    # assume the output argument is a file name first
    output_file_path = Path(args.output).resolve()
    # check if the output argument is a directory
    if '.' not in output_file_path.name:
        if not output_file_path.exists():
            raise Exception('The output directory does not exist!')
        if input_file_path.is_dir():
            raise Exception('Please specify a output file when input is a directory!')
        output_file_path = (output_file_path / input_file_path.name).with_suffix('.prx')

    # if args.debug:
    #     print(package_files)
    #     print(input_file_path)
    #     print(output_file_path)

    # this flag is set to true if any files have changed since last package
    repackage = False

    # check if compression cache has to be updated
    if args.compress:
        for file in package_files:
            # check if the source file is more recent thant the compressed file
            compressed_file_path = file.with_suffix(file.suffix + '_compressed')
            if compressed_file_path.is_file() and compressed_file_path.stat().st_mtime > file.stat().st_mtime and args.cache:
                print(F"Skipping file '{compressed_file_path}'")
                continue
            # update the compression cache
            with open(file, 'rb') as inp, open(compressed_file_path, 'wb') as out:
                print(F"Compressing file '{compressed_file_path}'")
                data = lzss.compress(inp.read())
                out.write(data)
            repackage = True

    if args.cache:
        # check if the build txt file has been updated since last package
        if input_file_path.stat().st_mtime > output_file_path.stat().st_mtime:
            print('DEBUG: The build file has changed!')
            repackage = True
        # check if any files have been updated since last package
        for file in package_files:
            if file.stat().st_mtime > output_file_path.stat().st_mtime:
                print(F"DEBUG: The file has changed! '{file}'")
                repackage = True
        # we dont need to do anything 
        if not repackage:
            print(F"Skipping unmodified file '{output_file_path}'")
            return

    # generate the container file
    generate_container_file(output_file_path, package_files, args)


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='prepack is a tool for packing game assets!')
    parser.add_argument('input', metavar='package.txt [source/]', nargs='?', type=str, help='build file or directory')
    parser.add_argument('--output', metavar='package.prx [pre/]', type=str, help='output file name or directory')
    parser.add_argument('--compress', action='store_true', help='compress files with LZSS')
    parser.add_argument('--thugpro', action='store_true', help='deal with source/output relative paths in build files')
    parser.add_argument('--cache', action='store_true', help='only compress files that have changed since last package')
    parser.add_argument('--debug', action='store_true', help=argparse.SUPPRESS)
    _args = parser.parse_args()
    try:
        prepack(_args)
        sys.exit(0)
    except Exception as e:
        print(e)
        sys.exit(1)

# $ prepack build.txt --output path/pre/ --compress --thugpro
# $ prepack source/ --output path/pre/package.prx
