import argparse
from pathlib import Path
from thps_formats.scripting2.qb import QB
from thps_formats.shared.enums import GameVersion


# ------------------------------------------------------------------------------
def compile(args):
    params = {
        'debug': args.debug,
        'game': GameVersion.THUGPRO_WIN
    }

    print('---- args -----------------------------------------------------------')
    print(args)
    defines = []
    if args.defines:
        definespath = Path(args.defines).resolve()
        if not definespath.is_file():
            raise Exception('Expected defines argument to be a file!')
        with open(definespath, 'r') as file:
            for index, line in enumerate(file):
                line = line.strip()
                line = line.split('//')[0]
                if not line:
                    continue
                name = line.split('#define ').pop()
                defines.append(name)

    print('---- defines --------------------------------------------------------')
    print(defines)

    if args.recursive:
        sourcepath = Path(args.compile).resolve()
        if sourcepath.is_file():
            print('Expected input argument to be a directory!')
            raise Exception('Expected input argument to be a directory!')
        
        outputpath = Path(args.output).resolve()
        if outputpath.is_file():
            print('Expected output argument to be a directory!')
            print('Expected output argument to be a directory!')
            raise Exception('Expected output argument to be a directory!')

        print('---- recursive ------------------------------------------------------')
        for sourcefile in sourcepath.rglob('*.q'):
            if sourcefile.is_file():
                outputfile = outputpath / sourcefile.relative_to(sourcepath).with_suffix('.qb')
                outputfile.parent.mkdir(exist_ok=True, parents=True)
                print(sourcefile)
                print(outputfile)
                QB.from_file(sourcefile, params, defines).to_file(outputfile, params)

    else:
        qb = QB.from_file(args.compile, params, [])
        qb.to_file(args.compile.replace('.q', '.qb'), params)


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='qcomp blahhh')
    parser.add_argument('--defines', metavar='defines.txt', required=False, type=str, help='A text file with #defines...')
    parser.add_argument('--recursive', action='store_true', help='Recursive...')
    parser.add_argument('-c', '--compile', metavar='example.q', required=True, type=str, help='The script to compile...')
    parser.add_argument('-o', '--output', metavar='output', required=False, type=str, help='Output directory...')
    parser.add_argument('--debug', action='store_true', help='include debug information')
    args = parser.parse_args()
    try:
        compile(args)
    except Exception as e:
        print(e)
