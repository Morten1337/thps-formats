import sys
import shutil
import argparse
from pathlib import Path


# ------------------------------------------------------------------------------
def parse_assets_file(assets_file):
    assets = []
    with assets_file.open('r') as file:
        for line in file:
            cleaned_line = line.split(';')[0].strip()
            if not cleaned_line:
                continue
            file_name = Path(cleaned_line)
            assets.append(file_name)
    return assets


# ------------------------------------------------------------------------------
def copy(args):

    if not args.input:
        raise Exception('No input file or directory specified!')

    if not args.output:
        raise Exception('No output file or directory specified!')

    assets_file = Path(args.input).resolve()
    output_path = Path(args.output).resolve()
    source_path = Path().cwd().resolve()

    assets = parse_assets_file(assets_file)

    for asset in assets:
        source_file = source_path / asset
        if not source_file.is_file():
            print(f"Warning: Couldn't find the file! {source_file}")
            continue

        relative_path = asset.relative_to('source')
        output_file = output_path / relative_path
        output_file.parent.mkdir(exist_ok=True, parents=True)
        try:
            print(f"Copying file '{source_file}' to '{output_file}'")
            shutil.copyfile(source_file, output_file)
        except shutil.SameFileError:
            pass
        except Exception as e:
            print(f"Error copying '{source_file}': {e}")


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
