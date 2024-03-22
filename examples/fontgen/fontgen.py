import os
import sys
import argparse
from pathlib import Path
#sys.path.insert(0, os.path.abspath('../../'))
from thps_formats.graphics.font import Font


# ------------------------------------------------------------------------------
def generate(args):

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
    args = parser.parse_args()
    try:
        generate(args)
        sys.exit(0)
    except Exception as e:
        print(e)
        sys.exit(1)
