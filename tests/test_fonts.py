from thps_formats.graphics.font import Font
from thps_formats.shared.enums import GameVersion


def test_fonts():
	params = {}
	font = Font.from_xml('./tests/data/fonts/eras.fnt', params)
	assert font is not None
	assert font.to_file('./tests/data/fonts/eras.fnt.xbx', params)
