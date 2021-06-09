import math

import arcade
from arcade import *


import interaction
import turn
import constants as c


class Action:

    def __init__(self, data: tuple = ("default", "default")):
        """
        :param data: this is the input data for the Action family of classes, put everything needed for your Action here
        """
        self.data = data

    def act(self):
        print(self.data[0])

    def input_act(self, inputs: tuple = ("default", "default")):
        print(self.data[0], inputs)


class HideTabAction(Action):
    def act(self):
        if self.data[0] in self.data[1]:
            self.data[1].remove(self.data[0])


class ToggleTabAction(Action):
    def act(self):
        if self.data[0] not in self.data[1]:
            self.data[1].append(self.data[0])
        else:
            self.data[1].remove(self.data[0])


class ToggleTextureAction(Action):
    def __toggle__(self, direction=1):
        if self.data[0] is not None:
            if self.data[0].texture in self.data[1]:
                index = (self.data[1].index(self.data[0].texture) + direction) % len(self.data[1])
            else:
                index = 0
            self.data[0].texture = self.data[1][index]

    def act(self):
        self.__toggle__()

    def input_act(self, inputs: tuple = (1, None)):
        direction = -int(inputs[0] / abs(inputs[0]))
        self.__toggle__(direction)


class TriggerEventAction(Action):

    def act(self):
        self.data[0](1, *self.data[1:])

    def input_act(self, inputs: tuple = (1,)):
        direction = -int(inputs[0] / abs(inputs[0]))
        self.data[0](direction, *self.data[1:])


class Button(Sprite):

    def __init__(self, texture: arcade.Texture, pressed_texture: arcade.Texture = None,
                 pos=(0, 0), action: Action = Action(), secondary_action: Action = None, text: str = ""):
        super().__init__()
        self.center_x = c.round_to_x(pos[0], 5 * c.SPRITE_SCALE)
        self.center_y = c.round_to_x(pos[1], 5 * c.SPRITE_SCALE)
        self.action = action
        self.secondary_action = secondary_action
        self.texture = texture
        self.base_texture = texture
        self.pressed_texture = pressed_texture
        self.text = text
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
            if self.secondary_action is not None:
                self.secondary_action.act()

    def on_scroll(self, value):
        self.action.input_act([value])
        if self.secondary_action is not None:
            self.secondary_action.input_act([value])

    def draw_hit_box(self, color: Color = arcade.color.WHITE, line_thickness: float = 1):
        arcade.draw_text(self.text, self.center_x, self.center_y, color, anchor_x='center', anchor_y='center')


class Tab(Sprite):

    def __init__(self, texture, rel_x, rel_y, game_view, movable: bool = True,
                 button_data: tuple = (), tab_data: tuple = (), display_data: tuple = ()):
        super().__init__(scale=c.SPRITE_SCALE)
        # Parent Element List
        self.parent_list = game_view.ui_elements

        # Misc
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

        # Displays (Text, or low function decals)
        self.display_data = display_data
        self.displays = self.process_displays()

        # The tab pos based on the relative x and y important for scaling screen sizes.
        self.center_x = c.round_to_x(game_view.window.view_x + rel_x, 5 * c.SPRITE_SCALE)
        self.center_y = c.round_to_x(game_view.window.view_y + rel_y, 5 * c.SPRITE_SCALE)

        game_view.ui_elements.append(self)

    def process_buttons(self):
        buttons = arcade.SpriteList()
        if self.button_data is not None:
            texture = arcade.load_texture("assets/ui/ui_pieces.png", x=230, width=230, height=90)
            for data in self.button_data:
                text = data.get('text', '')
                texture = data.get('texture', texture)
                second = data.get('secondary', None)
                pos = (self.center_x + data['x'] * c.SPRITE_SCALE, self.center_y + data['y'] * c.SPRITE_SCALE)
                buttons.append(Button(texture, pos=pos, action=data['action'], secondary_action=second, text=text))
        return buttons

    def process_displays(self):
        displays = arcade.SpriteList()
        for data in self.display_data:
            textures = []
            for text_data in data['textures']:
                texture = arcade.load_texture(data['text_location'], x=text_data['x'], y=text_data.get('y', 0),
                                              width=text_data['width'], height=text_data['height'])
                textures.append(texture)
            pos = self.center_x + data['x'] * c.SPRITE_SCALE, self.center_y + data['y'] * c.SPRITE_SCALE
            displays.append(Display(textures, pos))
        return displays

    def load_buttons(self, button_data):
        buttons = list(self.button_data)
        for button in button_data:
            if button not in self.button_data:
                buttons.append(button)

        self.button_data = tuple(buttons)
        self.buttons = self.process_buttons()

    def strip_buttons(self, button_data):
        buttons = list(self.button_data)
        for button in button_data:
            if button in self.button_data:
                buttons.remove(button)

        self.button_data = tuple(buttons)
        self.buttons = self.process_buttons()

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
            self.center_x = c.round_to_x(self.center_x + dx, 5 * c.SPRITE_SCALE)
            self.center_y = c.round_to_x(self.center_y + dy, 5 * c.SPRITE_SCALE)

    def on_scroll(self, value):
        hover = arcade.check_for_collision_with_list(self.game_view.window.mouse, self.buttons)
        if len(hover):
            hover[-1].on_scroll(value)

    def draw(self):
        super().draw()
        self.buttons.draw()
        self.buttons.draw_hit_boxes()
        self.displays.draw()

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
                button.center_x = new_value + self.button_data[index]['x'] * c.SPRITE_SCALE

            for index, display in enumerate(self.displays):
                display.center_x = new_value + self.display_data[index]['x'] * c.SPRITE_SCALE

            for tab in self.tabs:
                if tab not in self.parent_list:
                    tab.center_x = self.game_view.window.view_x + tab.rel_x

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
                button.center_y = new_value + self.button_data[index]['y'] * c.SPRITE_SCALE

            for index, display in enumerate(self.displays):
                display.center_y = new_value + self.display_data[index]['y'] * c.SPRITE_SCALE

            for tab in self.tabs:
                if tab not in self.parent_list:
                    tab.center_y = self.game_view.window.view_y + tab.rel_y

    center_y = property(_get_center_y, _set_center_y)


class Display(arcade.Sprite):

    def __init__(self, textures: tuple, pos=(0, 0)):
        super().__init__()
        self.scale = c.SPRITE_SCALE
        self.textures = textures
        self.texture = textures[0]
        self.center_x, self.center_y = pos


class DisplayTab(Tab):

    def __init__(self, game_view):
        text_data = [{'x': 230, 'y': 180, 'width': 230, 'height': 90},
                     {'x': 460, 'y': 180, 'width': 230, 'height': 90},
                     {'x': 690, 'y': 180, 'width': 230, 'height': 90}]
        display_data = [{'x': -95, 'y': 70, 'text_location': 'assets/ui/ui_pieces.png',
                         'textures': text_data},
                        {'x': -95, 'y': -5, 'text_location': 'assets/ui/ui_pieces.png',
                         'textures': text_data},
                        {'x': -95, 'y': -80, 'text_location': 'assets/ui/ui_pieces.png',
                         'textures': text_data}]

        super().__init__(arcade.load_texture("assets/ui/ui_split.png", x=4120, width=1030, height=650),
                         c.SCREEN_WIDTH - 126, 105, game_view, False, display_data=display_data)
        self.button_data = [{"x": 65, "y": 70,
                             "action": ToggleTextureAction((self.displays[0], self.displays[0].textures)),
                             'secondary': TriggerEventAction((game_view.map_handler.display_handler.mod_state, 'wall')),
                             'texture': arcade.load_texture("assets/ui/ui_pieces.png",
                                                            x=0, y=180, width=230, height=90)},
                            {"x": 65, "y": -5,
                             "action": ToggleTextureAction((self.displays[1], self.displays[1].textures)),
                             'secondary': TriggerEventAction((game_view.map_handler.display_handler.mod_state, 'cover'))
                             , 'texture': arcade.load_texture("assets/ui/ui_pieces.png",
                                                              x=0, y=180, width=230, height=90)},
                            {"x": 65, "y": -80,
                             "action": ToggleTextureAction((self.displays[2], self.displays[2].textures)),
                             'secondary': TriggerEventAction((game_view.map_handler.display_handler.mod_state, 'poi')),
                             'texture': arcade.load_texture("assets/ui/ui_pieces.png",
                                                            x=0, y=180, width=230, height=90)}]
        self.buttons = self.process_buttons()


class InvTab(Tab):

    def __init__(self, game_view):
        button_data = [{"x": 280, "y": 165,
                        "action": ToggleTabAction((self, game_view.ui_elements)),
                        'texture': arcade.load_texture("assets/ui/ui_pieces.png", x=0, width=230, height=90)}]
        super().__init__(arcade.load_texture("assets/ui/ui_split.png", x=1030, width=1030, height=650),
                         216, 948, game_view, button_data=button_data)


class TalkTab(Tab):

    def __init__(self, game_view):
        button_data = [{"x": 440, "y": 140,
                        "action": ToggleTabAction((self, game_view.ui_elements)),
                        'texture': arcade.load_texture("assets/ui/ui_pieces.png", x=0, width=230, height=90)}]
        super().__init__(arcade.load_texture("assets/ui/ui_split.png", x=2060, width=1030, height=650),
                         c.SCREEN_WIDTH - 567, 123, game_view, button_data=button_data)

        self.convo: interaction.Node = game_view.convo_handler
        self.current_node: interaction.Node = self.convo
        self.node_buttons = []
        self.node_button_text = []
        self.find_node_buttons()

    def next_node(self, direction,
                  node):
        self.current_node = node
        self.current_node.reset()
        self.find_node_buttons()

    def find_node_buttons(self):
        self.strip_buttons(self.node_buttons)
        node_buttons = []
        button_text = []
        for index, key_node in enumerate(self.current_node.inputs.items()):
            button = {"x": -390, "y": 50 - 75 * index,
                      "action": TriggerEventAction((self.next_node, key_node[1])),
                      'texture': arcade.load_texture("assets/ui/ui_pieces.png", x=230, y=90, width=230, height=90)}
            button_text.append([key_node[0], button['x'], button['y']])
            node_buttons.append(button)
        self.node_button_text = button_text
        self.node_buttons = node_buttons

    def draw(self):
        super().draw()
        self.current_node.draw(self.center_x, self.center_y)
        # TODO: Create a proper text system and intergrate into displays. Then remove this placeholder system.
        if len(self.node_buttons) and self.node_buttons[0] in self.button_data:
            for text in self.node_button_text:
                draw_text(text[0], self.center_x + text[1] * c.SPRITE_SCALE, self.center_y + text[2] * c.SPRITE_SCALE,
                          arcade.color.WHITE, anchor_y='top')

    def on_press(self, point):
        super().on_press(point)
        if self.current_node.on_press():
            self.load_buttons(self.node_buttons)


class ActionTab(Tab):

    def __init__(self, game_view):
        text_data = [{'x': 460, 'y': 90, 'width': 230, 'height': 90},
                     {'x': 690, 'y': 0, 'width': 230, 'height': 90}]
        display_data = [
            {'x': -330, 'y': 70, 'text_location': 'assets/ui/ui_pieces.png',
                         'textures': text_data},
            {'x': -330, 'y': -5, 'text_location': 'assets/ui/ui_pieces.png',
                         'textures': text_data},
            {'x': -330, 'y': -80, 'text_location': 'assets/ui/ui_pieces.png',
                         'textures': text_data},
            {'x': 10, 'y': 70, 'text_location': 'assets/ui/ui_pieces.png',
                         'textures': text_data},
            {'x': 10, 'y': -5, 'text_location': 'assets/ui/ui_pieces.png',
                         'textures': text_data},
            {'x': 10, 'y': -80, 'text_location': 'assets/ui/ui_pieces.png',
                         'textures': text_data}]
        button_data = [{'x': -175 + ((math.floor(index/3))*340), 'y': 75-((index % 3)*75),
                        "action": TriggerEventAction((game_view.select_action, action)),
                        "texture": arcade.load_texture("assets/ui/ui_pieces.png", x=230, y=90, width=230, height=90),
                        'text': f"{action[:1].upper()}{action[1:]}"} for index, action in enumerate(turn.ACTIONS)]
        button_data.append({"x": 370, "y": 105,
                            "action": ToggleTabAction((self, game_view.ui_elements)),
                            'texture': arcade.load_texture("assets/ui/ui_pieces.png", x=0, width=230, height=90)})

        super().__init__(arcade.load_texture("assets/ui/ui_split.png", x=3090, width=1030, height=650),
                         669, 99, game_view, button_data=button_data, display_data=display_data)


class MasterTab(Tab):

    def __init__(self, game_view):
        tab_data = (InvTab(game_view),
                    TalkTab(game_view),
                    ActionTab(game_view),
                    DisplayTab(game_view))
        button_data = ({"x": -220, "y": 120, "text": "INV",
                        "action": ToggleTabAction((tab_data[0], game_view.ui_elements))},
                       {"x": -220, "y": -15, "text": "TALK",
                        "action": ToggleTabAction((tab_data[1], game_view.ui_elements))},
                       {"x": -220, "y": -150, "text": "ACT",
                        "action": ToggleTabAction((tab_data[2], game_view.ui_elements))})

        super().__init__(arcade.load_texture("assets/ui/ui_split.png", width=1030, height=650),
                         204, 195, game_view, False, button_data, tab_data)
