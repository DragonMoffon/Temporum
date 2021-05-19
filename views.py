import arcade

import constants as c
import mapdata
import player
import isometric
import ui
import turn
import interaction
import shaders


class Mouse(arcade.Sprite):

    def __init__(self):
        super().__init__("assets/ui/cursor.png", c.SPRITE_SCALE)
        self._points = (-22.5, 22.5), (-22, 22.5), (-22, 22), (-22.5, 22)


class TemporumWindow(arcade.Window):
    """
    The Game Window, This holds the view and any constant variables as this will always be the same object.
    """

    def __init__(self):
        super().__init__(c.SCREEN_WIDTH, c.SCREEN_HEIGHT, c.WINDOW_NAME, fullscreen=c.FULLSCREEN)
        arcade.set_background_color(arcade.color.BLACK)
        self.set_mouse_visible(False)
        self.mouse = Mouse()

        # View data
        self.view_x = c.round_to_x(-c.SCREEN_WIDTH/2, 5*c.SPRITE_SCALE)
        self.view_y = c.round_to_x(-c.SCREEN_HEIGHT/2, 5*c.SPRITE_SCALE)

        # The Views
        self.game = GameView()
        self.title = TitleView()

        # Always start with the title
        self.show_view(self.title)

    def on_key_press(self, symbol: int, modifiers: int):
        # At all times the ESCAPE key will close the game.
        if symbol == arcade.key.X:
            self.close()

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        self.mouse.center_x = self.view_x + x + self.mouse.width/2
        self.mouse.center_y = self.view_y + y - self.mouse.height/2


class GameView(arcade.View):
    """
    The GameView is the real game, it is where the gameplay will take place.
    """

    def __init__(self):
        self.window: TemporumWindow
        super().__init__()
        # Map Handler
        self.map_handler = mapdata.MapHandler()

        # Conversation Handler
        self.convo_handler = interaction.load_conversation()
        print(self.convo_handler)

        # The player info
        self.player = player.Player(9, 18, self.map_handler.ground_layer, self)
        c.iso_append(self.player)

        # Mouse Select
        self.select_tile = player.Select(0, 0, 0.1, self.map_handler.map_size)
        c.iso_append(self.select_tile)

        self.selected_tile: player.Selected = None

        # Ui Stuff
        self.ui_elements = arcade.SpriteList()
        self.master_tab = ui.MasterTab(self)
        self.pressed = None

        # Turn handler
        self.turn_handler = turn.TurnHandler(self, self.player, [])

        # keys for held checks
        self.shift = False

        # Debugging tools
        self.test_sprite = arcade.Sprite("assets/iso_tile_refrence.png", scale=5)
        self.test_list = arcade.SpriteList()
        self.test_list.append(self.test_sprite)

        # Shader Programs
        """
        # Debugging shader
        self.test_program, self.buffer, self.description, self.triangle_geometry \
            = shaders.setup_fullscreen_shader(self.window.ctx, "shaders/isometric_test_fs.glsl")
        """

        # Last action: reorder the shown isometric sprites
        c.ISO_LIST.reorder_isometric()

    def on_draw(self):
        arcade.start_render()
        c.ISO_LIST.draw()
        arcade.draw_point(0, 0, arcade.color.RAW_UMBER, 5)
        for element in self.ui_elements:
            element.draw()
        self.turn_handler.draw()
        if self.player.check_path is not None:
            prev_node = None
            for index, node in enumerate(self.player.check_path):
                if prev_node is not None:
                    px, py, pz = isometric.cast_to_iso(prev_node.location[0], prev_node.location[1])

                    loss_mod = 0
                    if self.player.current_path is not None and self.shift:
                        loss_mod = len(self.player.current_path)
                    nx, ny, nz = isometric.cast_to_iso(node.location[0], node.location[1])

                    if index < self.player.action_handler.calculate_remaining() - loss_mod:
                        arcade.draw_line(px, py-55,
                                         nx, ny-55,
                                         arcade.color.ELECTRIC_BLUE, 2)
                    else:
                        arcade.draw_line(px, py-55,
                                         nx, ny-55,
                                         arcade.color.RADICAL_RED, 2)
                prev_node = node

        if self.player.current_path is not None:
            prev_node = None
            for node in self.player.current_path:
                if prev_node is not None:
                    px, py, pz = isometric.cast_to_iso(prev_node.location[0], prev_node.location[1])
                    nx, ny, nz = isometric.cast_to_iso(node.location[0], node.location[1])
                    arcade.draw_line(px, py - 55,
                                     nx, ny - 55,
                                     (27, 40, 149), 2)
                prev_node = node

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

        self.window.mouse.draw()
        self.map_handler.debug_draw()

    def on_update(self, delta_time: float):
        self.turn_handler.update()

    def on_show(self):
        view_x, view_y = self.window.view_x, self.window.view_y
        arcade.set_viewport(view_x, view_x+c.SCREEN_WIDTH, view_y, view_y+c.SCREEN_HEIGHT)

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.LSHIFT:
            self.shift = True
        elif self.turn_handler.current_actor.actor == self.player:
            self.player.on_key_press(symbol, self.shift)

    def on_key_release(self, _symbol: int, _modifiers: int):
        if _symbol == arcade.key.LSHIFT:
            self.shift = False

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        map_size = self.map_handler.map_size
        y_mod = ((160-c.FLOOR_TILE_THICKNESS)*c.SPRITE_SCALE)
        e_x, e_y = isometric.cast_from_iso(self.window.view_x + x, self.window.view_y + y + y_mod, map_size)
        if 0 <= e_x < self.map_handler.map_width and 0 <= e_y < self.map_handler.map_height:
            if e_x != self.select_tile.e_x or e_y != self.select_tile.e_y:
                self.select_tile.new_pos(e_x, e_y, map_size)
                self.map_handler.run_display('mouse', e_x, e_y)
                c.ISO_LIST.reorder_isometric()
            if self.turn_handler.current_actor is not None and self.turn_handler.current_actor.actor == self.player:
                self.player.find_move(self.select_tile, self.shift)

    def on_mouse_drag(self, x: float, y: float, dx: float, dy: float, _buttons: int, _modifiers: int):
        if _buttons == 2:
            rx = c.round_to_x(dx, 5*c.SPRITE_SCALE)
            ry = c.round_to_x(dy, 5*c.SPRITE_SCALE)
            self.window.view_x -= rx
            self.window.view_y -= ry
            self.ui_elements.move(-rx, -ry)
            arcade.set_viewport(self.window.view_x, self.window.view_x + c.SCREEN_WIDTH,
                                self.window.view_y, self.window.view_y + c.SCREEN_HEIGHT)
        elif _buttons == 1:
            dragged = arcade.check_for_collision_with_list(self.window.mouse, self.ui_elements)
            if self.pressed is None and len(dragged):
                dragged[-1].on_drag(dx, dy, (self.window.view_x + x, self.window.view_y + y))
                self.pressed = dragged[-1]
            elif self.pressed is not None and self.pressed.pressed_button is None:
                self.pressed.on_drag(dx, dy, (self.window.view_x + x, self.window.view_y + y))

    def on_mouse_release(self, x: float, y: float, button: int,
                         modifiers: int):
        if self.pressed is not None:
            self.pressed.on_release((self.window.view_x + x, self.window.view_y + y))
        self.pressed = None

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        if button == 1:
            pressed = arcade.check_for_collision_with_list(self.window.mouse, self.ui_elements)
            if len(pressed):
                self.pressed: ui.Tab = pressed[-1]
                self.pressed.on_press((self.window.view_x + x, self.window.view_y + y))
            else:
                if self.selected_tile is None:
                    self.selected_tile = player.Selected(self.select_tile.e_x, self.select_tile.e_y, 0.1,
                                                         self.map_handler.map_size)
                    c.ISO_LIST.append(self.selected_tile)
                    c.ISO_LIST.reorder_isometric()
                else:
                    self.selected_tile.new_pos(self.select_tile.e_x, self.select_tile.e_y,
                                               self.map_handler.map_size)
                if self.player.check_path is not None:
                    self.player.set_move(self.shift)

    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int):
        pressed = arcade.check_for_collision_with_list(self.window.mouse, self.ui_elements)
        if len(pressed):
            self.pressed: ui.Tab = pressed[-1]
            self.pressed.on_scroll(scroll_y)


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
