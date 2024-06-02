import os
import sys
import argparse
import traceback
from pathlib import Path

import thps_formats.encoding.lzss as lzss
from thps_formats.utils.writer import BinaryWriter
from thps_formats.utils.reader import BinaryReader
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
def extract_package_files(package_path, output_path, args):
    with open(package_path, 'rb') as inp:
        reader = BinaryReader(inp)

        package_size = reader.read_uint32()
        package_version = reader.read_uint32()
        file_count = reader.read_uint32()

        for _ in range(file_count):
            data_size = reader.read_uint32()
            compressed_size = reader.read_uint32()
            file_path_length = reader.read_uint32()
            file_path_checksum = reader.read_uint32()
            file_path = reader.read_bytes(file_path_length).decode('utf-8', 'ignore').split('\x00', 1)[0]

            if compressed_size == 0:
                file_data = reader.read_bytes(data_size)
            else:
                file_data = lzss.decompress(reader.read_bytes(compressed_size))

            padding = (4 - (reader.stream.tell() % 4)) % 4
            if padding != 0:
                reader.seek(padding, os.SEEK_CUR)

            output_file_path = Path(output_path) / file_path
            output_file_path.parent.mkdir(parents=True, exist_ok=True)

            if compressed_size == 0:
                print(F"--- [{package_path.stem}] extracting uncompressed file at {output_file_path}")
            else:
                print(F"--- [{package_path.stem}] extracting compressed file at {output_file_path}")

            with open(output_file_path, 'wb') as out:
                out.write(file_data)


# ------------------------------------------------------------------------------
def create_package_file(output_file_path, package_files, args):

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
def preunpack(args):

    # --------------------------------------------------------------------------
    packages = []

    # --------------------------------------------------------------------------
    if not args.input:
        raise Exception('No input file or directory specified!')

    # --------------------------------------------------------------------------
    if not args.output:
        raise Exception('No output file or directory specified!')

    # --------------------------------------------------------------------------
    # check if the input argument is a file name (prx file)
    input_file_path = Path(args.input).resolve()
    if '.' in input_file_path.name or input_file_path.is_file():
        if not input_file_path.exists():
            raise Exception('The input file does not exist!')
        packages.append(input_file_path.resolve())
    else:
        # check if the input argument is a directory
        if not input_file_path.exists():
            raise Exception('The input directory does not exist!')
        if not input_file_path.is_dir():
            raise Exception('The input directory does not exist!')
        for input_file_name in input_file_path.rglob('*.prx'):
            if input_file_name.is_file():
                packages.append(input_file_name.resolve())

    # --------------------------------------------------------------------------
    output_path = Path(args.output).resolve()
    if not output_path.exists():
        raise Exception('The output directory does not exist!')
    if not output_path.is_dir():
        raise Exception('Please specify an output directory!')

    # --------------------------------------------------------------------------
    # generate the container file
    for package in packages:
        extract_package_files(package, output_path, args)


# ------------------------------------------------------------------------------
def prepack(args):

    if args.unpack:
        return preunpack(args)

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
    create_package_file(output_file_path, package_files, args)


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='prepack is a tool for packing game assets!')
    parser.add_argument('input', metavar='package.txt [source/]', nargs='?', type=str, help='build file or directory')
    parser.add_argument('--output', metavar='package.prx [pre/]', type=str, help='output file name or directory')
    parser.add_argument('--compress', action='store_true', help='compress files with LZSS')
    parser.add_argument('--thugpro', action='store_true', help='deal with source/output relative paths in build files')
    parser.add_argument('--cache', action='store_true', help='only compress files that have changed since last package')
    parser.add_argument('--debug', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--unpack', action='store_true', help=argparse.SUPPRESS) # undocumented
    _args = parser.parse_args()
    try:
        prepack(_args)
        sys.exit(0)
    except Exception:
        traceback.print_exc(limit=2, file=sys.stdout)
        sys.exit(1)

# $ prepack build.txt --output path/pre/ --compress --thugpro
# $ prepack source/ --output path/pre/package.prx

# $ prepack data/pre/ --output data/ --unpack
# $ prepack data/pre/qb_scripts.prx --output data/ --unpack
