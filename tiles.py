import isometric

"""
This is a "storage" script. It is doing the job is Json file which I will implement later. However for now it stores all
the data itself.
"""

TEXTURES = {
    1: isometric.IsoTexture("assets/iso_tile_refrence_wall_sheet.png", .0, .0, 0, 0, 160, 320),
    2: isometric.IsoTexture("assets/iso_tile_refrence_wall_sheet.png", .0, 20.0, 0, 320, 160, 320),
    3: isometric.IsoTexture("assets/iso_tile_refrence_wall_sheet.png", .0, 20.0, 160, 320, 160, 320),
    4: isometric.IsoTexture("assets/iso_tile_refrence_wall_sheet.png", .0, 20.0, 320, 320, 160, 320),
    5: isometric.IsoTexture("assets/iso_tile_refrence_wall_sheet.png", .0, 20.0, 480, 320, 160, 320),
    6: isometric.IsoTexture("assets/iso_tile_refrence_wall_sheet.png", .0, 20.0, 0, 640, 160, 320),
    7: isometric.IsoTexture("assets/iso_tile_refrence_wall_sheet.png", .0, 20.0, 160, 640, 160, 320),
    8: isometric.IsoTexture("assets/iso_tile_refrence_wall_sheet.png", .0, 20.0, 320, 640, 160, 320),
    9: isometric.IsoTexture("assets/iso_tile_refrence_wall_sheet.png", .0, 20.0, 480, 640, 160, 320),
    10: isometric.IsoTexture("assets/iso_tile_refrence_wall_sheet.png", .0, 20.0, 0, 960, 160, 320),
    11: isometric.IsoTexture("assets/iso_tile_refrence_wall_sheet.png", .0, 20.0, 160, 960, 160, 320),
    12: isometric.IsoTexture("assets/iso_tile_refrence_wall_sheet.png", .0, 20.0, 320, 960, 160, 320),
    13: isometric.IsoTexture("assets/iso_tile_refrence_wall_sheet.png", .0, 20.0, 480, 960, 160, 320),
    14: isometric.IsoTexture("assets/iso_tile_refrence_wall_sheet.png", .0, 20.0, 0, 1280, 160, 320),
    15: isometric.IsoTexture("assets/iso_tile_refrence_wall_sheet.png", .0, 20.0, 160, 1280, 160, 320)
            }


def find_iso_data(tile_id):
    return TEXTURES[tile_id]
