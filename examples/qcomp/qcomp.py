import argparse
from thps_formats.scripting2 import QB
from thps_formats.shared.enums import GameVersion


# ------------------------------------------------------------------------------
def compile(args):
    params = {
        'debug': args.debug,
        'game': GameVersion.THUGPRO_WIN
    }
    qb = QB.from_file(args.compile, params, [])
    qb.to_file(args.compile.replace('.q', '.qb'), params)


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='qcomp blahhh')
    parser.add_argument('-c', '--compile', metavar='example.q', required=True, type=str, help='The script to compile.')
    parser.add_argument('--debug', action='store_true', help='include debug information')
    args = parser.parse_args()
    compile(args)
