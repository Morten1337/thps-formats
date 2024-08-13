from pathlib import Path as Path

import thps_formats.encoding.lzss as lzss
from thps_formats.utils.diff import find_diff_chunk


# ------------------------------------------------------------------------------
def test_compression():

    files = [
        Path('./tests/data/control_setup.qb').resolve(),
        Path('./tests/data/thugpro_net.qb').resolve(),
        Path('./tests/data/thugpro_leveleditor.qb').resolve(),
        Path('./tests/data/thug_pro_dev_menu.qb').resolve(),
    ]

    for x in range(10):
        for f in files:
            with open(f, 'rb') as inp, open(f.with_suffix('.qb_compressed'), 'wb') as out:
                print(F"Compressing file '{f}'")
                out.write(lzss.compress(inp.read()))
                assert find_diff_chunk(f.with_suffix('.qb_compressed'), f.with_suffix('.qb_compressed_pretool')) is False
