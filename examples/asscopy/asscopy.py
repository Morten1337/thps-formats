import sys
import shutil
import argparse
from pathlib import Path


# ------------------------------------------------------------------------------
def parse_assets_file(input_file_path):
    assets = []
    with input_file_path.open('r') as file:
        for line in file:
            cleaned_line = line.split(';')[0].strip()
            if not cleaned_line:
                continue
            file_name = Path(cleaned_line).resolve()
            if not file_name.is_file():
                raise Exception(F"Couldn't find the file with name! {file_name}")
            assets.append(file_name)
    return assets


# ------------------------------------------------------------------------------
def copy(args):

    assets = []

    if not args.input:
        raise Exception('No input file or directory specified!')

    if not args.output:
        raise Exception('No output file or directory specified!')

    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()
    source_path = Path().cwd().resolve()

    assets.extend(parse_assets_file(input_path))

    for asset in assets:
        output_file = output_path / asset
        source_file = source_path / asset
        output_file.parent.mkdir(exist_ok=True, parents=True)
        try:
            print(F"Copying file '{asset}'")
            shutil.copyfile(source_file, output_file)
        except shutil.SameFileError:
            pass


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='prepack is a tool for packing game assets!')
    parser.add_argument('input', metavar='assets.txt', nargs='?', type=str, help='asset list file')
    parser.add_argument('--output', metavar='output/data/textures', type=str, help='output directory')
    _args = parser.parse_args()
    try:
        copy(_args)
        sys.exit(0)
    except Exception as e:
        print(e)
        sys.exit(1)

# %THUGPRO_TOOLS_PATH%\asscopy %THUGPRO_BUILD_PATH%\textures.txt --output %THUGPRO_OUTPUT_PATH%
