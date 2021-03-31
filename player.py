import arcade
import isometric
import constants as c

PLAYER_ISO_DATA = isometric.IsoTexture("assets/iso_player_character.png", .0, 150.0, 0, 0, 160, 320)


class Player(isometric.IsoSprite):

    def __init__(self, e_x, e_y, e_map, game_view):
        x, y, z = isometric.cast_to_iso(e_x, e_y, e_map, z_mod=0.5)
        super().__init__(e_x, e_y, x, y, z, PLAYER_ISO_DATA)
        self.ground_map = e_map
        self.game_view = game_view

    def on_key_press(self, key):
        moved = False
        if key == arcade.key.UP and self.ground_map[self.e_y][self.e_x+1]:
            self.e_x += 1
            moved = True
        elif key == arcade.key.DOWN and self.ground_map[self.e_y][self.e_x-1]:
            self.e_x -= 1
            moved = True
        elif key == arcade.key.LEFT and self.ground_map[self.e_y+1][self.e_x]:
            self.e_y += 1
            moved = True
        elif key == arcade.key.RIGHT and self.ground_map[self.e_y-1][self.e_x]:
            self.e_y -= 1
            moved = True

        if moved:
            self.center_x, self.center_y, self.center_z = isometric.cast_to_iso(self.e_x, self.e_y,
                                                                                self.ground_map, z_mod=.5)
            self.center_x += self.mod_x*c.SPRITE_SCALE
            self.center_y += self.mod_y*c.SPRITE_SCALE
            self.game_view.shown_tiles.reorder_isometric()
