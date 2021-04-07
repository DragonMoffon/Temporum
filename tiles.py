import json

import isometric


def load_textures():
    with open("data/tiles.json") as file:
        files, tiles = json.load(file).values()
        textures = {}
        for index, tile in enumerate(tiles):
            texture = isometric.IsoTexture(files[tile['texture']], tile['mod_x'], tile['mod_y'],
                                           tile['start_x'], tile['start_y'], tile['width'], tile['height'])
            tile_data = {'texture': texture, 'directions': tile['directions']}
            textures[index+1] = tile_data
    return textures


TEXTURES = load_textures()


def find_iso_data(tile_id):
    return TEXTURES[tile_id]
