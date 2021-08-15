
import time

import arcade
from typing import List, Tuple

import constants as c
import mapdata
import player
import isometric
import ui
import turn
import interaction
import algorithms


class Mouse(arcade.Sprite):

    def __init__(self, window):
        super().__init__("assets/ui/cursor.png", c.SPRITE_SCALE)
        self._points = (-22.5, 22.5), (-22, 22.5), (-22, 22), (-22.5, 22)
        self.window = window
        self.rel_x = 0
        self.rel_y = 0
        self.e_x = 0
        self.e_y = 0

    def _get_center_x(self) -> float:
        """ Get the center x coordinate of the sprite. """
        return self._position[0]

    def _set_center_x(self, new_value: float):
        """ Set the center x coordinate of the sprite. """
        if new_value != self._position[0]:
            self.rel_x = new_value - self.window.view_x

            self.clear_spatial_hashes()
            self._point_list_cache = None
            self._position = (new_value, self._position[1])
            self.add_spatial_hashes()

            for sprite_list in self.sprite_lists:
                sprite_list.update_location(self)

    center_x = property(_get_center_x, _set_center_x)

    def _get_center_y(self) -> float:
        """ Get the center y coordinate of the sprite. """
        return self._position[1]

    def _set_center_y(self, new_value: float):
        """ Set the center y coordinate of the sprite. """
        if new_value != self._position[1]:
            self.rel_y = new_value - self.window.view_y

            self.clear_spatial_hashes()
            self._point_list_cache = None
            self._position = (self._position[0], new_value)
            self.add_spatial_hashes()

            for sprite_list in self.sprite_lists:
                sprite_list.update_location(self)

    center_y = property(_get_center_y, _set_center_y)


class TemporumWindow(arcade.Window):
    """
    The Game Window, This holds the view and any constant variables as this will always be the same object.
    """

    def __init__(self):
        super().__init__(c.SCREEN_WIDTH, c.SCREEN_HEIGHT, c.WINDOW_NAME, fullscreen=c.FULL_SCREEN)
        arcade.set_background_color(arcade.color.BLACK)

        # View data
        self.zoom = 1
        self._view_x = c.round_to_x(-c.SCREEN_WIDTH / 2, 5 * c.SPRITE_SCALE)
        self._view_y = c.round_to_x(-c.SCREEN_HEIGHT / 2, 5 * c.SPRITE_SCALE)

        # Mouse
        self.set_mouse_visible(False)
        self.mouse = Mouse(self)

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
        self.mouse.center_x = c.round_to_x(self.view_x + x + self.mouse.width / 2, 3)
        self.mouse.center_y = c.round_to_x(self.view_y + y - self.mouse.height / 2, 3)

    @property
    def view_x(self):
        return self._view_x

    @view_x.setter
    def view_x(self, value):
        self._view_x = value
        self.mouse.center_x = value + self.mouse.rel_x

    @property
    def view_y(self):
        return self._view_y

    @view_y.setter
    def view_y(self, value):
        self._view_y = value
        self.mouse.center_y = value + self.mouse.rel_y


class GameView(arcade.View):
    """
    The GameView is the real game, it is where the gameplay will take place.
    """

    def __init__(self):
        self.window: TemporumWindow
        super().__init__()

        # Turn System
        self.turn_handler = turn.TurnHandler([], self)

        # The Current Ai info
        self.current_ai = []

        # The player info
        self.player = player.Player(25, 25, self)
        self.turn_handler.new_action_handlers([self.player.action_handler])
        c.iso_append(self.player)
        c.set_player(self.player)

        # Map Handler
        self.map_handler = mapdata.MapHandler(self)
        self.map_handler.load_map()

        # Setting player grid now that the map_handler has been initialised.
        self.player.set_grid(self.map_handler.full_map)

        # Conversation Handler
        self.convo_handler = interaction.load_conversation()

        # Mouse Select
        self.select_tile = player.Select(0, 0)
        c.iso_append(self.select_tile)

        self.selected_tile: player.Selected = None

        self.action_tab = ui.ActionTab(self)

        # Ui Stuff
        self.ui_elements = arcade.SpriteList()
        self.tabs = (ui.TalkTab(self),)

        self.tabs[0].center_x = c.round_to_x(self.window.view_x + c.SCREEN_WIDTH // 2, 5 * c.SPRITE_SCALE)
        self.tabs[0].center_y = c.round_to_x(self.window.view_y + c.SCREEN_HEIGHT // 2, 5 * c.SPRITE_SCALE)
        self.master_tab = ui.MasterTab(self)
        self.pressed = None
        self.ui_tabs_over = []

        # keys for held checks
        self.shift = False

        # Debugging tools
        self.test_list = arcade.SpriteList()

        # player action data
        self.selected_action = 'move'
        self.pending_action = None
        self.current_handler = None

        # View code
        self.motion = False
        self.motion_start = 0
        self.motion_length = 1.10
        self.pending_motion: List[Tuple[float, float]] = []
        self.current_motion = None
        self.current_motion_start: Tuple[float, float] = (self.window.view_x, self.window.view_y)

        # Last action: reorder the shown isometric sprites
        c.iso_changed()

        # set view port

    def move_view(self, dx, dy):
        # Round to fit the pixels of sprites
        rx = c.round_to_x(dx, 5 * c.SPRITE_SCALE)
        ry = c.round_to_x(dy, 5 * c.SPRITE_SCALE)

        # move the view by this amount
        self.window.view_x -= rx
        self.window.view_y -= ry

        # Move the ui and set the viewport.
        self.ui_elements.move(-rx, -ry)
        arcade.set_viewport(self.window.view_x, self.window.view_x + c.SCREEN_WIDTH,
                            self.window.view_y, self.window.view_y + c.SCREEN_HEIGHT)

    def set_view(self, x, y):
        # find the change x and y then round to fit the pixels of sprites
        dx = c.round_to_x(x - self.window.view_x, 5 * c.SPRITE_SCALE)
        dy = c.round_to_x(y - self.window.view_y, 5 * c.SPRITE_SCALE)

        # Set the view to the rounded inputs
        self.window.view_x = c.round_to_x(x, 5 * c.SPRITE_SCALE)
        self.window.view_y = c.round_to_x(y, 5 * c.SPRITE_SCALE)

        # Move the ui and set the viewport
        self.ui_elements.move(dx, dy)
        arcade.set_viewport(self.window.view_x, self.window.view_x + c.SCREEN_WIDTH,
                            self.window.view_y, self.window.view_y + c.SCREEN_HEIGHT)

    def on_draw(self):
        self.map_handler.map.vision_handler.draw_prep()
        arcade.start_render()

        c.GROUND_LIST.draw()

        # Middle Shaders Between floor and other isometric sprites
        if self.map_handler is not None:
            self.map_handler.draw()

        c.ISO_LIST.draw()

        self.turn_handler.on_draw()
        if self.pending_action is not None:
            self.pending_action.draw()

        for element in self.ui_elements:
            element.draw()

        self.action_tab.draw()
#
        # Debugging of the map_handler
        # self.map_handler.debug_draw(True)
        if self.player is not None and 1 == 2:
            p_location = self.player.e_x, self.player.e_y
            px, py, z = isometric.cast_to_iso(*p_location)
            seen = []
            for tile in c.WALLS:
                if tile is not None:
                    dx, dy = p_location[0]-tile.location[0], p_location[1]-tile.location[1]
                    nx, ny = abs(dx), abs(dy)
                    sign_x, sign_y = 1 if dx > 0 else -1, 1 if dy > 0 else -1

                    p = list(p_location)
                    final = p_location
                    ix, iy = 0, 0
                    while ix < nx or iy < ny:
                        current = self.map_handler.full_map[p[0], p[1]]

                        if current is not None:
                            if current not in seen:
                                seen.append(current)

                            if (0.5 + ix) * ny < (0.5 + iy) * nx:
                                p[0] += sign_x
                                ix += 1
                                direction = c.DIRECTIONS[sign_x, 0]
                            else:
                                p[1] += sign_y
                                iy += 1
                                direction = c.DIRECTIONS[0, sign_y]

                            if not current.vision[direction]:
                                final = tuple(current.location)
                                break
                        else:
                            break

                    x, y, z = isometric.cast_to_iso(*final)
                    arcade.draw_line(x, y-60, px, py-60, arcade.color.RADICAL_RED)

        self.map_handler.debug_draw()
        self.window.mouse.draw()

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.L:
            self.map_handler.map.vision_handler.calculate()

    def on_update(self, delta_time: float):
        # Debug FPS
        # print(f"FPS: {1/delta_time}")
        self.turn_handler.on_update(delta_time)
        if self.current_handler != self.turn_handler.current_handler:
            self.current_handler = self.turn_handler.current_handler
            if self.current_handler is self.player.action_handler:
                if self.selected_tile is not None:
                    self.selected_tile.new_pos(self.player.e_x, self.player.e_y)
                self.action_tab.find_actions(self.player.e_x, self.player.e_y)

        if self.turn_handler.current_handler != self.player.action_handler:
            self.turn_handler.current_handler.actor.update()

        if self.motion:
            t = (time.time() - self.motion_start) / self.motion_length
            if t >= 1:
                self.set_view(*self.current_motion)
                self.motion = False
            else:
                motion_diff = self.current_motion[0] - self.current_motion_start[0], \
                              self.current_motion[1] - self.current_motion_start[1]
                adj_t = 2 * t
                if adj_t < 1:
                    move = 0.5 * adj_t ** 3
                else:
                    adj_t -= 2
                    move = 0.5 * (adj_t ** 3 + 2)
                dx = self.current_motion_start[0] + (move * motion_diff[0])
                dy = self.current_motion_start[1] + (move * motion_diff[1])
                self.set_view(dx, dy)

        elif len(self.pending_motion):
            self.current_motion = self.pending_motion.pop(0)
            if abs(self.current_motion[0] - self.window.view_x) > 15 and \
                    abs(self.current_motion[1] - self.window.view_y) > 15:
                self.current_motion_start = (self.window.view_x, self.window.view_y)
                self.motion_start = time.time()
                self.motion = True

        self.player.update_animation(delta_time)

    def on_show(self):
        self.set_view(self.player.center_x - c.SCREEN_WIDTH / 2, self.player.center_y - c.SCREEN_HEIGHT / 2)

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        y_mod = ((160 - c.FLOOR_TILE_THICKNESS) * c.SPRITE_SCALE)
        e_x, e_y = isometric.cast_from_iso(self.window.view_x + x, self.window.view_y + y + y_mod)
        self.ui_tabs_over = arcade.check_for_collision_with_list(self.window.mouse, self.ui_elements)
        if 0 <= e_x < self.map_handler.map_width and 0 <= e_y < self.map_handler.map_height \
                and not len(self.ui_tabs_over):
            if e_x != self.select_tile.e_x or e_y != self.select_tile.e_y:
                self.select_tile.new_pos(e_x, e_y)
                c.iso_changed()
                self.action_tab.on_mouse_motion(e_x, e_y)
        elif self.player.e_x != self.select_tile.e_x or self.player.e_y != self.select_tile.e_y:
            self.select_tile.new_pos(self.player.e_x, self.player.e_y)
            c.iso_changed()

    def on_mouse_drag(self, x: float, y: float, dx: float, dy: float, _buttons: int, _modifiers: int):
        if _buttons == 2:
            self.move_view(dx, dy)
            if len(self.pending_motion):
                self.pending_motion = []
            self.current_motion = None
            self.motion = False
        elif _buttons == 1:
            self.ui_tabs_over = arcade.check_for_collision_with_list(self.window.mouse, self.ui_elements)
            if self.pressed is None and len(self.ui_tabs_over):
                self.ui_tabs_over[-1].on_drag(dx, dy, (self.window.view_x + x, self.window.view_y + y))
                self.pressed = self.ui_tabs_over[-1]
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

    def new_bot(self, bot):
        new_bot = algorithms.create_bot(bot.x, bot.y, self.map_handler.full_map)
        self.current_ai.append(new_bot)
        c.iso_append(new_bot)
        self.turn_handler.new_action_handlers([new_bot.action_handler])

    def reset_bots(self):
        self.turn_handler.remove_action_handlers(map(lambda bot: bot.action_handler, self.current_ai))
        c.iso_strip(self.current_ai)
        self.current_ai = []

    def set_bots(self, bots):
        self.turn_handler.new_action_handlers(map(lambda bot: bot.action_handler, self.current_ai))
        self.current_ai = bots


class TitleView(arcade.View):
    """
    The TitleView is the title
    """

    def __init__(self):
        super().__init__()
        self.image = arcade.Sprite("assets/Title.png", c.SPRITE_SCALE,
                                   center_x=c.SCREEN_WIDTH/2, center_y=c.SCREEN_HEIGHT/2)

    def on_draw(self):
        arcade.start_render()
        self.image.draw()
        arcade.draw_text("Press Enter to start",
                         c.SCREEN_WIDTH//2,
                          c.SCREEN_HEIGHT // 2 - 25, arcade.color.WHITE)

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.ENTER:
            self.window.show_view(self.window.game)


def main():
    window = TemporumWindow()
    # c.start_music()
    arcade.run()
