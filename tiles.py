import json
from dataclasses import dataclass

import arcade

import isometric


@dataclass()
class PieceData:
    texture: arcade.Texture
    hidden: arcade.Texture
    relative_pos: tuple[int, int]
    mod_w: float


@dataclass()
class TileData:
    pos_mods: tuple[float, float, float]
    directions: tuple[bool, bool, bool, bool]
    pieces: list[PieceData]


def load_textures():
    """
    Loads all the tiles from the tile data json file.
    :return: It returns a dictionary with the tile data for every tile in game.
    """
    with open("data/tiles.json") as file:
        # Firstly it open the json file and splits it into the files for the texture, with the width and height of
        # each tile that is gotten from this texture, and the tile data for each tile.
        files, tiles = json.load(file).values()

        # It then iterates through every tile in the tile data, creating a TileData object that is used in sprite
        # creation.
        textures = {}
        for index, tile in enumerate(tiles[:-1]):
            # It creates an variable for each part of the tile.

            # The texture data take from the files list.
            texture_data = files[tile['texture']]

            # The secondary texture data, this is for if the item should be hidden.
            hidden_data = files[tile['hidden']]

            # This is the modifiers to the x, y, and w of the sprite. This is used to position the tile properly
            pos_mods = tile['mods']

            # The movement directions for this tile. the default here is in-case the tile data does not specify this.
            # Since the movement algorithm uses an AND to calculate if a direction if viable then if none is specified
            # than in can be assumed that the tile is accessible from any direction.
            directions = tile.get('directions', [1, 1, 1, 1])

            # This is the data for each piece of a tile. The tile can actually be made up of many sprites that can go
            # across different e_x and e_y co-ordinates.
            pieces_data: list[dict] = tile['pieces']

            # This loop creates the piece data.
            pieces = []
            for piece in pieces_data:
                # This is the relative  euler position of a piece relative to the starting
                # piece which is generally piece with the lowest screen pos (on screen y axis)
                relative_pos = tuple(piece.get('relative_pos', [0, 0]))

                # a possible unique w mod in case the pieces need to be rendered in a specific order.
                mod_w = piece.get('mod_w', 0)
                texture = arcade.load_texture(texture_data['file'], piece['start_x'], piece['start_y'],
                                              texture_data['width'], texture_data['height'])
                hidden = arcade.load_texture(hidden_data['file'], piece['start_x'], piece['start_y'],
                                              hidden_data['width'], hidden_data['height'])
                pieces.append(PieceData(texture, hidden, relative_pos, mod_w))

            textures[index+1] = TileData(pos_mods, directions, pieces)
    return textures


TEXTURES = load_textures()


def find_iso_data(tile_id):

    return TEXTURES[tile_id]


def find_iso_sprites(tile_id, pos_data):
    iso_textures = find_iso_data(tile_id)
    tiles = []
    if isinstance(iso_textures['texture'], tuple):
        for texture in iso_textures['texture']:
            iso_texture = {'texture': texture, 'directions': iso_textures['directions']}
            iso_x, iso_y, iso_z = isometric.cast_to_iso(*pos_data)
            tile = isometric.IsoSprite(pos_data[0], pos_data[1], iso_texture)
            tiles.append(tile)
    else:
        iso_x, iso_y, iso_z = isometric.cast_to_iso(*pos_data)
        tile = isometric.IsoSprite(pos_data[0], pos_data[1], iso_textures)
        tiles.append(tile)

    return tiles


