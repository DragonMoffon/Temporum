import json
from dataclasses import dataclass

import arcade


@dataclass()
class PieceData:
    texture: arcade.Texture
    hidden: arcade.Texture
    relative_pos: tuple
    mod_w: float


@dataclass()
class TileData:
    pos_mods: tuple
    directions: tuple
    vision: tuple
    pieces: list
    actions: tuple


def load_textures(location: str = 'tiles.json'):
    """
    Loads all the tiles from the provided json file. This is generally tiles.json. But it also can load other tiles
    if provided.
    :return: It returns a dictionary with the tile data for every tile in game.
    """
    with open(f"data/{location}") as file:
        # Firstly it open the json file and splits it into the files for the texture, with the width and height of
        # each tile that is gotten from this texture, and the tile data for each tile.
        files, tiles = json.load(file).values()

        # It then iterates through every tile in the tile data, creating a TileData object that is used in sprite
        # creation.
        textures = {}
        for index, tile in enumerate(tiles[:-1]):
            # It creates a variable for each part of the tile.

            # The texture data take from the files list.
            texture_data = files[tile['texture']]

            # The secondary texture data, this is for if the item should be hidden.
            hidden_data = files[tile.get('hidden', tile['texture'])]

            # The key for the dict.
            # only really needed in special edge cases so that is why the key defaults to the index
            key = tile.get('id', index+1)

            # This is the modifiers to the x, y, and w of the sprite. This is used to position the tile properly
            pos_mods = tile['mods']

            # The movement directions for this tile. the default here is in-case the tile data does not specify this.
            # Since the movement algorithm uses an AND to calculate if a direction if viable then if none is specified
            # than in can be assumed that the tile is accessible from any direction.
            directions = tile.get('directions', [1, 1, 1, 1])

            # The vision directions for this tile. this is for the raycating. In most cases the  directions are
            # identical to the directions, only items such as the laser gate and the terminal do not block LOS even
            # though they stop movement
            vision = tile.get('vision', directions)

            # The actions are the possible actions an actor in combat can take based on the tiles.
            actions = tuple(tile.get('actions', []))

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
                # If it is not found in the dict it is assumed to be 0
                mod_w = piece.get('mod_w', 0)

                file = files[piece.get('other_texture', tile['texture'])]

                # Create the two textures and create the piece data.
                texture = arcade.load_texture(file['file'], piece['start_x'], piece['start_y'],
                                              file['width'], file['height'])

                if hidden_data == texture_data:
                    hidden = None
                else:
                    hidden = arcade.load_texture(hidden_data['file'], piece['start_x'], piece['start_y'],
                                                 hidden_data['width'], hidden_data['height'])
                pieces.append(PieceData(texture, hidden, relative_pos, mod_w, ))

            # Create the TileData and add to the dict.
            textures[key] = TileData(pos_mods, directions, vision, pieces, actions)
    return textures


TEXTURES = load_textures()
OTHER_TEXTURES = load_textures('special_tiles.json')


def find_iso_data(tile_id):

    return TEXTURES[tile_id]


