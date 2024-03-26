import sys
import argparse
from pathlib import Path
from thps_formats.scripting2.qb import QB
from thps_formats.shared.enums import GameVersion


# ------------------------------------------------------------------------------
def parse_defines_from_file(filename):
    defines = []
    definespath = Path(filename).resolve()
    if not definespath.is_file():
        print(f"WARN: The defines file does not exist! '{filename}'")
        return defines
    with definespath.open('r') as file:
        for line in file:
            cleaned_line = line.split('//')[0].strip()
            if cleaned_line.startswith('#define '):
                definename = cleaned_line.replace('#define ', '', 1)
                defines.append(definename)
    return defines


# ------------------------------------------------------------------------------
def compile(args):
    params = {
        'debug': args.debug,
        'game': GameVersion.THUGPRO_WIN
    }

    if not args.input:
        raise Exception('No input script file name or directory specified!')
 
    defines = []
    if args.defines:
        for item in args.defines.split(','):
            if item:
                if '.' in item:
                    defines.extend(parse_defines_from_file(item))
                else:
                    defines.append(item)

    inputpath = Path(args.input).resolve()
    if '.' in inputpath.name:

        if not inputpath.exists():
            raise Exception('The input file does not exist!')

        if args.output:
            outputpath = Path(args.output).resolve()
            if '.' not in outputpath.name: # is not file
                outputpath = outputpath / (inputpath.stem + '.qb')
        else:
            outputpath = Path(args.input).resolve().with_suffix('.qb') # derive output name from source file name

        print(F"Compiling file '{inputpath}'")
        QB.from_file(inputpath, params, defines).to_file(outputpath, params)

    else:

        if not inputpath.exists():
            raise Exception('The input directory does not exist!')

        outputpath = Path(args.output if args.output else args.input).resolve()
        if '.' in outputpath.name:
            raise Exception('Expected output to be a directory!')

        if args.recursive:
            files = inputpath.rglob('*.q')
        else:
            files = inputpath.glob('*.q')

        for inputfile in files:
            if inputfile.is_file():
                outputfile = outputpath / inputfile.relative_to(inputpath).with_suffix('.qb')
                outputfile.parent.mkdir(exist_ok=True, parents=True)
                if args.cache:
                    if inputfile.stat().st_mtime > outputfile.stat().st_mtime:
                        print(F"Compiling file '{inputfile}'")
                        QB.from_file(inputfile, params, defines).to_file(outputfile, params)
                    else:
                        print(F"Skipping unmodified file '{inputfile}'")
                else:
                    print(F"Compiling file '{inputfile}'")
                    QB.from_file(inputfile, params, defines).to_file(outputfile, params)


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='qcompy blahhh')
    parser.add_argument('input', metavar='filename.q [scripts/]', nargs='?', type=str, help='source file name or directory')
    parser.add_argument('--output', metavar='filename.qb [scripts/]', type=str, help='output file name or directory')
    parser.add_argument('--recursive', action='store_true', help='recurse sub-directories if input is a directory')
    parser.add_argument('--defines', metavar='DEVELOPER,FOO [defines.txt]', type=str, help='directive name defines comma separated')
    parser.add_argument('--debug', action='store_true', help='include debug information')
    parser.add_argument('--cache', action='store_true', help='only compile files that have changed since last compile')
    args = parser.parse_args()
    try:
        compile(args)
        sys.exit(0)
    except Exception as e:
        print(e)
        sys.exit(1)

# $ qcompy file.q
# $ qcompy path/ --recursive
# $ qcompy path/ --recursive --defines defines.txt
# $ qcompy file.q --defines DEVLOPER,HELLO,SOMETHING
# $ qcompy file.q --defines DEVLOPER,HELLO,SOMETHING --debug
