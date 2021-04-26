import arcade
from arcade import *
import constants as c


class Action:

    def __init__(self, data: tuple = "test"):
        self.data = data

    def act(self):
        print(self.data)


class ToggleTabAction(Action):
    def act(self):
        if self.data[0] not in self.data[1]:
            self.data[1].append(self.data[0])
        else:
            self.data[1].remove(self.data[0])


class HideTabAction(Action):
    def act(self):
        if self.data[0] in self.data[1]:
            self.data[1].remove(self.data[0])


class Button(Sprite):

    def __init__(self,  texture: arcade.Texture, pressed_texture: arcade.Texture = None,
                 pos=(0, 0),  action: Action = Action("Default")):
        super().__init__()
        self.center_x = c.round_to_x(pos[0], 5*c.SPRITE_SCALE)
        self.center_y = c.round_to_x(pos[1], 5*c.SPRITE_SCALE)
        self.action = action
        self.texture = texture
        self.base_texture = texture
        self.pressed_texture = pressed_texture
        self.scale = c.SPRITE_SCALE

    def on_press(self):
        if self.pressed_texture is not None and self.texture != self.pressed_texture:
            self.texture = self.pressed_texture
        else:
            self.texture = self.base_texture

    def on_release(self, over):
        self.texture = self.base_texture
        if over:
            self.action.act()


class Tab(Sprite):

    def __init__(self, texture, rel_x, rel_y, game_view, movable: bool = True,
                 button_data: tuple = (), tab_data: tuple = ()):
        super().__init__(scale=c.SPRITE_SCALE)
        # Parent Element List
        self.parent_list = game_view.ui_elements

        # Misc
        if button_data is None:
            button_data = []
        self.texture = texture
        self.game_view = game_view
        self.rel_x = rel_x
        self.rel_y = rel_y

        # Whether the tab can be moved or not
        self.movable = movable

        # Tab Buttons
        self.button_data = button_data
        self.buttons = self.process_buttons()
        self.pressed_button: Button = None

        # Child Tabs
        self.tabs = tab_data

        # The tab pos based on the relative x and y important for scaling screen sizes.
        self.center_x = c.round_to_x(game_view.window.view_x + rel_x, 5*c.SPRITE_SCALE)
        self.center_y = c.round_to_x(game_view.window.view_y + rel_y, 5*c.SPRITE_SCALE)

    def process_buttons(self):
        buttons = arcade.SpriteList()
        if self.button_data is not None:
            texture = arcade.load_texture("assets/ui/ui_pieces.png", x=525, width=180, height=90)
            for data in self.button_data:
                if 'text' in data:
                    texture = data['text']
                button = Button(texture, pos=(self.center_x+data['x'], self.center_y+data['y']),
                                action=data['action'])
                buttons.append(button)
        return buttons

    def on_press(self, point):
        self.pressed_button = None
        for button in self.buttons:
            if button.collides_with_point(point):
                self.pressed_button = button
                break

    def on_release(self, point):
        if self.pressed_button is not None:
            self.pressed_button.on_release(self.pressed_button.collides_with_point(point))
            self.pressed_button = None

    def on_drag(self, dx, dy, point):
        self.on_press(point)
        if self.movable and self.pressed_button is None:
            self.center_x = c.round_to_x(self.center_x + dx, 5*c.SPRITE_SCALE)
            self.center_y = c.round_to_x(self.center_y + dy, 5*c.SPRITE_SCALE)

    def draw(self):
        super().draw()
        self.buttons.draw()
        self.buttons.draw()
        draw_point(self.center_x, self.center_y, arcade.color.RADICAL_RED, c.SPRITE_SCALE*5)

    def _get_center_x(self) -> float:
        """ Get the center y coordinate of the sprite. """
        return self._position[0]

    def _set_center_x(self, new_value: float):
        if new_value != self._position[0]:
            self.clear_spatial_hashes()
            self._point_list_cache = None
            self._position = (new_value, self._position[1])
            self.add_spatial_hashes()

            for sprite_list in self.sprite_lists:
                sprite_list.update_location(self)

            for index, button in enumerate(self.buttons):
                button.center_x = new_value + self.button_data[index]['x']

            for tab in self.tabs:
                if tab not in self.parent_list:
                    tab.center_x = self.game_view.window.view_x + tab.rel_x

            print("x", new_value-self.game_view.window.view_x)

    center_x = property(_get_center_x, _set_center_x)

    def _get_center_y(self) -> float:
        """ Get the center y coordinate of the sprite. """
        return self._position[1]

    def _set_center_y(self, new_value: float):
        if new_value != self._position[1]:
            self.clear_spatial_hashes()
            self._point_list_cache = None
            self._position = (self._position[0], new_value)
            self.add_spatial_hashes()

            for sprite_list in self.sprite_lists:
                sprite_list.update_location(self)

            for index, button in enumerate(self.buttons):
                button.center_y = new_value + self.button_data[index]['y']

            for tab in self.tabs:
                if tab not in self.parent_list:
                    tab.center_y = self.game_view.window.view_y + tab.rel_y

            print("y", new_value-self.game_view.window.view_y)

    center_y = property(_get_center_y, _set_center_y)


class InvTab(Tab):

    def __init__(self, game_view):
        button_data = [{"x": 285*c.SPRITE_SCALE, "y": 165*c.SPRITE_SCALE,
                        "action": ToggleTabAction((self, game_view.ui_elements)),
                        'text': arcade.load_texture("assets/ui/ui_pieces.png", x=350, width=180, height=90)}]
        super().__init__(arcade.load_texture("assets/ui/ui_split.png", x=1030, width=1030, height=650),
                         219, 945, game_view, button_data=button_data)


class TalkTab(Tab):

    def __init__(self, game_view):
        button_data = [{"x": 445*c.SPRITE_SCALE, "y": 140*c.SPRITE_SCALE,
                        "action": ToggleTabAction((self, game_view.ui_elements)),
                        'text': arcade.load_texture("assets/ui/ui_pieces.png", x=350, width=180, height=90)}]
        super().__init__(arcade.load_texture("assets/ui/ui_split.png", x=2060, width=1030, height=650),
                         1614, 123, game_view, button_data=button_data)


class ActionTab(Tab):

    def __init__(self, game_view):
        button_data = [{"x": 360 * c.SPRITE_SCALE, "y": 105 * c.SPRITE_SCALE,
                        "action": ToggleTabAction((self, game_view.ui_elements)),
                        'text': arcade.load_texture("assets/ui/ui_pieces.png", x=350, width=180, height=90)}]
        super().__init__(arcade.load_texture("assets/ui/ui_split.png", x=3090, width=1030, height=650),
                         669, 99, game_view, button_data=button_data)


class MasterTab(Tab):

    def __init__(self, game_view):
        tab_data = (InvTab(game_view),
                    TalkTab(game_view),
                    ActionTab(game_view))
        button_data = ({"x": -220*c.SPRITE_SCALE, "y": 120*c.SPRITE_SCALE,
                        "action": ToggleTabAction((tab_data[0], game_view.ui_elements))},
                       {"x": -220*c.SPRITE_SCALE, "y": -15*c.SPRITE_SCALE,
                        "action": ToggleTabAction((tab_data[1], game_view.ui_elements))},
                       {"x": -220*c.SPRITE_SCALE, "y": -150*c.SPRITE_SCALE,
                        "action": ToggleTabAction((tab_data[2], game_view.ui_elements))})

        super().__init__(arcade.load_texture("assets/ui/ui_split.png", width=1030, height=650),
                         204, 195, game_view, False, button_data, tab_data)
        game_view.ui_elements.append(self)
