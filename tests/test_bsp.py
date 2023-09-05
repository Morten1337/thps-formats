from thps_formats.experimental import BSP

bsp = BSP('./tests/data/ap.bsp')
scene = bsp.to_scene()
scene.to_file('ap.scn.xbx', 'THUG2PC')
