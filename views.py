import random
import time
import math

import arcade

import constants as c
import mapdata
import player
import isometric
import ui
import turn
import interaction
import algorithms
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
        self.mouse.center_x = c.round_to_x(self.view_x + x + self.mouse.width/2, 3)
        self.mouse.center_y = c.round_to_x(self.view_y + y - self.mouse.height/2, 3)


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

        # The player info
        self.player = player.Player(25, 25, self)
        c.iso_append(self.player)

        # A Test Bot
        self.test_bot = algorithms.create_bot(26, 25, algorithms.PathFindingGrid(self.map_handler))
        c.iso_append(self.test_bot)

        # Mouse Select
        self.select_tile = player.Select(0, 0)
        c.iso_append(self.select_tile)

        self.selected_tile: player.Selected = None

        self.action_tab = ui.ActionTab(self)

        # Ui Stuff
        self.ui_elements = arcade.SpriteList()
        self.tabs = (ui.InvTab(self),
                     ui.TalkTab(self),
                     ui.DisplayTab(self))
        self.master_tab = ui.MasterTab(self)
        self.pressed = None

        # Turn System
        self.turn_handler = turn.TurnHandler([self.player.action_handler, self.test_bot.action_handler], self)

        # keys for held checks
        self.shift = False

        # Debugging tools
        self.test_list = arcade.SpriteList()

        # player action data
        self.selected_action = 'move'
        self.pending_action = None
        self.current_handler = None

        # View code
        self.target_view_x = self.window.view_x
        self.target_view_y = self.window.view_y
        self.motion = False
        self.motion_start = 0
        self.motion_length = 1.5
        self.motion_view_start = None

        # Shader Programs

        # Debugging shader
        self.test_program, self.buffer, self.description, self.triangle_geometry \
             = shaders.setup_fullscreen_shader(self.window.ctx, "shaders/isometric_test_fs.glsl")

        # Last action: reorder the shown isometric sprites
        c.ISO_LIST.reorder_isometric()

    def move_view(self, dx, dy):
        # Round to fit the pixels of sprites
        rx = c.round_to_x(dx, 5 * c.SPRITE_SCALE)
        ry = c.round_to_x(dy, 5 * c.SPRITE_SCALE)

        # move the view by this amount
        self.window.view_x -= rx
        self.window.view_y -= ry

        # Reset the target view so no motion happens
        self.target_view_x = self.window.view_x
        self.target_view_y = self.window.view_y
        self.motion = False

        # Move the ui and set the viewport.
        self.ui_elements.move(-rx, -ry)
        arcade.set_viewport(self.window.view_x, self.window.view_x + c.SCREEN_WIDTH,
                            self.window.view_y, self.window.view_y + c.SCREEN_HEIGHT)

    def set_view(self, x, y):
        # find the change x and y then round to fit the pixels of sprites
        dx = c.round_to_x(x - self.window.view_x, 5*c.SPRITE_SCALE)
        dy = c.round_to_x(y - self.window.view_y, 5*c.SPRITE_SCALE)

        # Set the view to the rounded inputs
        self.window.view_x = c.round_to_x(x, 5*c.SPRITE_SCALE)
        self.window.view_y = c.round_to_x(y, 5*c.SPRITE_SCALE)

        # reset the target view so no motion happens
        self.target_view_x = self.window.view_x
        self.target_view_y = self.window.view_y
        self.motion = False

        # Move the ui and set the viewport
        self.ui_elements.move(dx, dy)
        arcade.set_viewport(self.window.view_x, self.window.view_x + c.SCREEN_WIDTH,
                            self.window.view_y, self.window.view_y + c.SCREEN_HEIGHT)

    def on_draw(self):
        arcade.start_render()
        c.ISO_LIST.draw()
        self.turn_handler.on_draw()
        if self.pending_action is not None:
            self.pending_action.draw()

        for element in self.ui_elements:
            element.draw()

        self.action_tab.draw()

        """if self.player.path_finding_grid is not None:
            dirs = ((0, -0.25), (0.25, 0), (0, 0.25), (-0.25, 0))
            for y_dex, point_row in enumerate(self.player.path_finding_grid.points):
                for x_dex, value in enumerate(point_row):
                    if value is not None:
                        for dir_dex, direction in enumerate(dirs):
                            t_x = x_dex + direction[0]
                            t_y = y_dex + direction[1]
                            iso_x, iso_y, iso_z = isometric.cast_to_iso(t_x, t_y)
                            if value.directions[dir_dex] is None:
                                arcade.draw_point(iso_x, iso_y - 60, arcade.color.RADICAL_RED, 5)
                            else:
                                arcade.draw_point(iso_x, iso_y - 60, arcade.color.WHITE, 5)"""

        # Debugging of the map_handler
        # self.map_handler.debug_draw(True)

        # Debugging Shader
        # self.test_program['screen_pos'] = self.window.view_x, self.window.view_y
        # self.triangle_geometry.render(self.test_program, mode=self.window.ctx.TRIANGLES)

        """
        # Debugging loop.
        for y_dex, y in enumerate(self.map_handler.ground_layer):
            for x_dex, x in enumerate(y):
                x_pos, y_pos, z_pos = isometric.cast_to_iso(x_dex, y_dex, self.map_handler.ground_layer)
                arcade.draw_text(f"{x_dex}, {y_dex}", x_pos, y_pos, arcade.color.WHITE)
        """

        self.map_handler.debug_draw()
        self.window.mouse.draw()

        arcade.draw_point(self.target_view_x+c.SCREEN_WIDTH/2, self.target_view_y+c.SCREEN_HEIGHT/2,
                          arcade.color.RIFLE_GREEN, 10)

    def on_update(self, delta_time: float):
        # Debug FPS
        # print(f"FPS: {1/delta_time}")
        self.turn_handler.on_update(delta_time)
        if self.current_handler != self.turn_handler.current_handler:
            self.current_handler = self.turn_handler.current_handler

        if self.turn_handler.current_handler == self.test_bot.action_handler and \
                self.test_bot.action_handler.current_action is None and self.test_bot.action_handler.initiative > 0:
            self.test_bot.load_paths()
            move_node = random.choice(self.test_bot.path_finding_data[2]
                                     [self.test_bot.action_handler.initiative]).location
            move_location = self.map_handler.full_map[move_node].pieces
            self.test_bot.action_handler.current_action = turn.ACTIONS['move'](move_location,
                                                                               self.test_bot.action_handler)

    def on_show(self):
        view_x, view_y = self.window.view_x, self.window.view_y
        arcade.set_viewport(view_x, view_x+c.SCREEN_WIDTH, view_y, view_y+c.SCREEN_HEIGHT)

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        y_mod = ((160-c.FLOOR_TILE_THICKNESS)*c.SPRITE_SCALE)
        e_x, e_y = isometric.cast_from_iso(self.window.view_x + x, self.window.view_y + y + y_mod)
        if 0 <= e_x < self.map_handler.map_width and 0 <= e_y < self.map_handler.map_height\
                and not len(arcade.check_for_collision_with_list(self.window.mouse, self.ui_elements)):
            if e_x != self.select_tile.e_x or e_y != self.select_tile.e_y:
                self.select_tile.new_pos(e_x, e_y)
                c.iso_changed()
                self.map_handler.run_display('mouse', e_x, e_y)
                self.action_tab.on_mouse_motion(e_x, e_y)
        elif self.player.e_x != self.select_tile.e_x or self.player.e_y != self.select_tile.e_y:
            self.select_tile.new_pos(self.player.e_x, self.player.e_y)
            c.iso_changed()
            self.map_handler.run_display('mouse', self.player.e_x, self.player.e_y)

    def on_mouse_drag(self, x: float, y: float, dx: float, dy: float, _buttons: int, _modifiers: int):
        if _buttons == 2:
            self.move_view(dx, dy)
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
        self.action_tab.on_mouse_press(button)
        if button == 1:
            pressed = arcade.check_for_collision_with_list(self.window.mouse, self.ui_elements)
            if len(pressed):
                self.pressed: ui.Tab = pressed[-1]
                self.pressed.on_press((self.window.view_x + x, self.window.view_y + y))
            else:
                if self.selected_tile is None:
                    self.selected_tile = player.Selected(self.select_tile.e_x, self.select_tile.e_y)
                    c.ISO_LIST.append(self.selected_tile)
                else:
                    self.selected_tile.new_pos(self.select_tile.e_x, self.select_tile.e_y)

    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int):
        pressed = arcade.check_for_collision_with_list(self.window.mouse, self.ui_elements)
        if len(pressed):
            self.pressed: ui.Tab = pressed[-1]
            self.pressed.on_scroll(scroll_y)
        else:
            self.action_tab.on_scroll(scroll_y/abs(scroll_y))

    def select_action(self, base_input, action: str):
        if action != self.selected_action:
            self.selected_action = action
            self.set_pending_action()
            self.process_action()

    def set_pending_action(self):
        if self.turn_handler.current_handler == self.player.action_handler \
           and self.selected_action is not None and self.player.action_handler.current_action is None:
            action_data = turn.ACTIONS[self.selected_action]
            self.pending_action = action_data([self.select_tile.e_x, self.select_tile.e_y],
                                              self.player.action_handler)

    def process_action(self):
        if self.turn_handler.current_handler == self.player.action_handler \
           and self.player.action_handler.current_action is None:
            self.player.action_handler.pending_action = self.pending_action

    def push_action(self):
        if self.player.action_handler.pending_action is not None:
            self.player.action_handler.current_action = self.player.action_handler.pending_action
            self.pending_action = None


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
