from pathlib import Path
from thps_formats.utils.reader import BinaryReader
from thps_formats.utils.diff import find_diff_chunk
from thps_formats.graphics.font import Font

# -------------------------------------------------------------------------------------------------
def test_fontgen():
    inputpath = Path("./tests/data/fonts/impact.fnt").resolve()
    outputpath = Path("./tests/data/fonts/impact.fnt.xbx").resolve()
    examplepath = Path("./tests/data/fonts/example.fnt.xbx").resolve()
    font = Font.from_xml(inputpath, {})
    assert font is not None
    assert font.to_file(outputpath, {})
    difference = find_diff_chunk(outputpath, examplepath)
    assert difference is False
