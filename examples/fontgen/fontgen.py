import sys
import argparse
from pathlib import Path
from thps_formats.graphics.font import Font


# ------------------------------------------------------------------------------
FONTGEN_VERSION_NUMBER = (1,0)

# ------------------------------------------------------------------------------
def generate(args):

    if args.version:
        print(F"fontgen v{FONTGEN_VERSION_NUMBER[0]}.{FONTGEN_VERSION_NUMBER[1]}")
        return

    if not args.input:
        raise Exception('No input file specified!')

    if not args.output:
        raise Exception('No output file or directory specified!')

    inputpath = Path(args.input).resolve()
    print(F"Generating font '{inputpath.name}'")
    font = Font.from_xml(inputpath, {})

    outputpath = Path(args.output).resolve()
    if outputpath.is_dir():
        outputpath = (outputpath / inputpath.name).with_suffix('.fnt.xbx')

    return font.to_file(outputpath, {})


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='fontgen generates fonts from bmfnt files!')
    parser.add_argument('input', metavar='arial.fnt', nargs='?', type=str, help='bmfnt file')
    parser.add_argument('--output', metavar='arial.fnt.xbx [fonts/]', type=str, help='output file name or directory')
    parser.add_argument('--version', action='store_true', help='print the current version number')
    args = parser.parse_args()
    try:
        generate(args)
        sys.exit(0)
    except Exception as e:
        print(e)
        sys.exit(1)
