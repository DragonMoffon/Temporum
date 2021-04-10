import arcade

import constants as c
import mapdata
import player
import isometric
import algorithms
import shaders


class TemporumWindow(arcade.Window):
    """
    The Game Window, This holds the view and any constant variables as this will always be the same object.
    """

    def __init__(self):
        super().__init__(c.SCREEN_WIDTH, c.SCREEN_HEIGHT, c.WINDOW_NAME, fullscreen=c.FULLSCREEN)
        arcade.set_background_color(arcade.color.BLACK)

        # The Views
        self.game = GameView()
        self.title = TitleView()

        # View data
        self.view_x = -c.SCREEN_WIDTH/2
        self.view_y = -c.SCREEN_HEIGHT/2

        # Always start with the title
        self.show_view(self.title)

    def on_key_press(self, symbol: int, modifiers: int):
        # At all times the ESCAPE key will close the game.
        if symbol == arcade.key.ESCAPE:
            self.close()


class GameView(arcade.View):
    """
    The GameView is the real game, it is where the gameplay will take place.
    """

    def __init__(self):
        super().__init__()
        # Map Handler
        self.map_handler = mapdata.MapHandler()

        # The tile lists
        self.shown_tiles = self.map_handler.apply_shown()

        # The player info
        self.player = player.Player(9, 18, self.map_handler.ground_layer, self)
        self.shown_tiles.append(self.player)

        # Mouse Select
        self.select_tile = player.Select(0, 0, self.map_handler.ground_layer)
        self.shown_tiles.append(self.select_tile)

        self.selected_tile: player.Selected = None

        # Shader Programs
        """
        # Debugging shader
        self.test_program, self.buffer, self.description, self.triangle_geometry \
            = shaders.setup_fullscreen_shader(self.window.ctx, "shaders/isometric_test_fs.glsl")
        """

        # Last action: reorder the shown isometric sprites
        self.shown_tiles.reorder_isometric()

    def on_draw(self):
        arcade.start_render()
        self.shown_tiles.draw()
        arcade.draw_point(0, 0, arcade.color.RAW_UMBER, 5)

        # Debugging of the map_handler
        # self.map_handler.debug_draw(True)
        """
        # Debugging Shader
        self.test_program['screen_pos'] = self.window.view_x, self.window.view_y
        self.triangle_geometry.render(self.test_program, mode=self.window.ctx.TRIANGLES)
        """

        """
        # Debugging loop.
        for y_dex, y in enumerate(self.map_handler.ground_layer):
            for x_dex, x in enumerate(y):
                x_pos, y_pos, z_pos = isometric.cast_to_iso(x_dex, y_dex, self.map_handler.ground_layer)
                arcade.draw_text(f"{x_dex}, {y_dex}", x_pos, y_pos, arcade.color.WHITE)
                """

    def on_update(self, delta_time: float):
        if self.player.current_path is not None:
            player = self.player
            current_node = self.map_handler.path_finding_map.points[player.e_y, player.e_x]
            if current_node in self.player.current_path:
                current_index = self.player.current_path.index(current_node)
                if current_index < len(self.player.current_path)-1:
                    next_node = self.player.current_path[current_index+1].location
                    self.player.new_pos(next_node[0], next_node[1],
                                        self.map_handler.ground_layer, self.shown_tiles)
                else:
                    self.player.current_path = None

    def on_show(self):
        view_x, view_y = self.window.view_x, self.window.view_y
        arcade.set_viewport(view_x, view_x+c.SCREEN_WIDTH, view_y, view_y+c.SCREEN_HEIGHT)

    def on_key_press(self, symbol: int, modifiers: int):
        self.player.on_key_press(symbol)

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        e_map = self.map_handler.ground_layer
        y_mod = ((160-c.FLOOR_TILE_THICKNESS)*c.SPRITE_SCALE)
        e_x, e_y = isometric.cast_from_iso(self.window.view_x + x, self.window.view_y + y + y_mod, e_map)
        if 0 <= e_x < self.map_handler.map_width and 0 <= e_y < self.map_handler.map_height:
            if e_x != self.select_tile.e_x or e_y != self.select_tile.e_y:
                self.select_tile.new_pos(e_x, e_y, e_map, self.shown_tiles, 0.2)
                self.shown_tiles.reorder_isometric()

    def on_mouse_drag(self, x: float, y: float, dx: float, dy: float, _buttons: int, _modifiers: int):
        if _buttons == 2:
            self.window.view_x -= round(dx)
            self.window.view_y -= round(dy)
            arcade.set_viewport(self.window.view_x, self.window.view_x + c.SCREEN_WIDTH,
                                self.window.view_y, self.window.view_y + c.SCREEN_HEIGHT)

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        if button == 1:
            if self.selected_tile is None:
                self.selected_tile = player.Selected(self.select_tile.e_x, self.select_tile.e_y,
                                                     self.map_handler.ground_layer)
                self.shown_tiles.append(self.selected_tile)
                self.shown_tiles.reorder_isometric()
            else:
                self.selected_tile.new_pos(self.select_tile.e_x, self.select_tile.e_y,
                                           self.map_handler.ground_layer, self.shown_tiles, 0.1)
            self.player.current_path = algorithms.path_2d(self.map_handler.path_finding_map,
                                                          (self.player.e_y, self.player.e_x),
                                                          (self.selected_tile.e_y, self.selected_tile.e_x))


class TitleView(arcade.View):
    """
    The TitleView is the title
    """
    def on_draw(self):
        arcade.start_render()
        arcade.draw_text("Press Enter to start", c.SCREEN_WIDTH/2, c.SCREEN_HEIGHT/2 - 25, arcade.color.WHITE)

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.ENTER:
            self.window.show_view(self.window.game)


def main():
    window = TemporumWindow()
    arcade.run()
