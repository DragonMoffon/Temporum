import json

import isometric


def load_textures():
    with open("data/tiles.json") as file:
        files, tiles = json.load(file).values()
        textures = {}
        for index, tile in enumerate(tiles[:-1]):
            if 'splits' in tile:
                t1, t2 = tile['splits']
                t1, t2 = textures[t1]['texture'], textures[t2]['texture']
                tile_data = {'texture': (t1, t2),
                             'directions': tile['directions']}
                textures[index+1] = tile_data
            else:
                file = files[tile['texture']]
                hidden = files[tile['hidden']]
                texture = isometric.IsoTexture(file['file'], hidden['file'], tile['mod_x'], tile['mod_y'],
                                               tile['mod_z'], tile['start_x'], tile['start_y'],
                                               file['width'], file['height'])
                tile_data = {'texture': texture, 'directions': tile['directions']}
                textures[index+1] = tile_data
    return textures


TEXTURES = load_textures()


def find_iso_sprites(tile_id, pos_data):
    iso_textures = find_iso_data(tile_id)
    tiles = []
    if isinstance(iso_textures['texture'], tuple):
        for texture in iso_textures['texture']:
            iso_texture = {'texture': texture, 'directions': iso_textures['directions']}
            iso_x, iso_y, iso_z = isometric.cast_to_iso(*pos_data)
            tile = isometric.IsoSprite(pos_data[0], pos_data[1], iso_x, iso_y, iso_z, iso_texture, pos_data[-1])
            tiles.append(tile)
    else:
        iso_x, iso_y, iso_z = isometric.cast_to_iso(*pos_data)
        tile = isometric.IsoSprite(pos_data[0], pos_data[1], iso_x, iso_y, iso_z, iso_textures, pos_data[-1])
        tiles.append(tile)

    return tiles


def find_iso_data(tile_id):

    return TEXTURES[tile_id]
