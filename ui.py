
import arcade


import interaction
import puzzle
import turn
import constants as c


class Action:

    def __init__(self, data: tuple = ("default",)):
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


class ShowTabAction(Action):
    def act(self):
        if self.data[0] not in self.data[1]:
            self.data[1].append(self.data[0])
            self.data[0].go_rel_pos()


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


class TriggerSimpleEventAction(Action):
    def act(self):
        self.data[0](*self.data[1:])


class TriggerDirectionEventAction(Action):

    def act(self):
        self.data[0](1, *self.data[1:])

    def input_act(self, inputs: tuple = (1,)):
        direction = -int(inputs[0] / abs(inputs[0]))
        self.data[0](direction, *self.data[1:])


class Button(arcade.Sprite):

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
        self.action.input_act((value,))
        if self.secondary_action is not None:
            self.secondary_action.input_act((value,))

    def draw_hit_box(self, color: arcade.Color = arcade.color.WHITE, line_thickness: float = 1):
        arcade.draw_text(self.text, self.center_x, self.center_y, color, anchor_x='center', anchor_y='center')


class Tab(arcade.Sprite):

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
            displays.append(Display(tuple(textures), pos))
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
            self.rel_x = self.rel_x + dx
            self.rel_y = self.rel_y + dy

    def on_scroll(self, value):
        hover = arcade.check_for_collision_with_list(self.game_view.window.mouse, self.buttons)
        if len(hover):
            hover[-1].on_scroll(value)

    def draw(self):
        super().draw()
        self.buttons.draw()
        self.buttons.draw_hit_boxes()
        self.displays.draw()

    def go_rel_pos(self):
        self.center_x = c.round_to_x(self.game_view.window.view_x + self.rel_x, 5*c.SPRITE_SCALE)
        self.center_y = c.round_to_x(self.game_view.window.view_y + self.rel_y, 5*c.SPRITE_SCALE)

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


ACTION_WORDS = {'move': arcade.Sprite("assets/ui/ui_text.png", c.SPRITE_SCALE,
                                      image_width=320, image_height=60, image_x=0),
                'end': arcade.Sprite("assets/ui/ui_text.png", c.SPRITE_SCALE,
                                      image_width=320, image_height=60, image_x=320),
                'shoot': arcade.Sprite("assets/ui/ui_text.png", c.SPRITE_SCALE,
                                       image_width=320, image_height=60, image_x=640),
                'interact': arcade.Sprite("assets/ui/ui_text.png", c.SPRITE_SCALE,
                                          image_width=320, image_height=60, image_x=960),
                'leave': arcade.Sprite("assets/ui/ui_text.png", c.SPRITE_SCALE,
                                       image_width=320, image_height=60, image_x=1280),
                None: arcade.Sprite("assets/ui/ui_text.png", c.SPRITE_SCALE,
                                    image_width=320, image_height=60, image_x=1600)}
ACTION_PRIORITY = {'move': 0, 'leave': 1, 'interact': 2, 'shoot': 3, 'end': 6}


class ActionTab(arcade.Sprite):

    def __init__(self, game_view):
        super().__init__("assets/ui/ui_split.png", c.SPRITE_SCALE, image_height=650, image_width=1030,
                         image_x=3090)
        self.game_view = game_view
        self.handle = False
        self.recheck = True
        self.actions = {}
        self.defaults = {'end': None}
        self.actions_ordered = []
        self.current_set = 0
        self.first_action: arcade.Sprite = None
        self.first_pending: turn.Action = None
        self.second_action: arcade.Sprite = None
        self.second_pending: turn.Action = None

    def draw(self):
        if self.game_view.player.action_handler != self.game_view.turn_handler.current_handler:
            self.recheck = True

        if self.game_view.player.action_handler == self.game_view.turn_handler.current_handler and\
                not len(self.game_view.ui_tabs_over) and self.game_view.player.action_handler.current_action is None:
            if self.recheck and self.game_view.player.action_handler.initiative:
                self.find_actions(self.game_view.window.mouse.e_x, self.game_view.window.mouse.e_y)
                self.recheck = False

            self.handle = True
            self.center_x = self.game_view.window.mouse.center_x + 120
            self.center_y = self.game_view.window.mouse.center_y - 90

            if self.first_pending is not None:
                self.first_pending.draw()
            if self.second_pending is not None:
                self.second_pending.draw()

            super().draw()
            if self.first_action is not None:
                self.first_action.center_x = self.center_x + 51
                self.first_action.center_y = self.center_y + 39
                self.first_action.draw()
            if self.second_action is not None:
                self.second_action.center_x = self.center_x + 51
                self.second_action.center_y = self.center_y - 36
                self.second_action.draw()

            return
        self.handle = False

    def find_actions(self, e_x, e_y):
        if self.handle and self.game_view.map_handler.full_map[e_x, e_y] is not None:
            self.actions = {**dict(self.game_view.map_handler.full_map[e_x, e_y].available_actions), **self.defaults}

            if len(self.actions) % 2:
                self.actions[None] = None
            self.actions_ordered = sorted(self.actions.keys(), key=lambda action: ACTION_PRIORITY.get(action, 10))
            if self.current_set >= len(self.actions):
                self.current_set = 0
            self.set_actions()

    def on_mouse_motion(self, e_x, e_y):
        self.find_actions(e_x, e_y)

    def on_mouse_press(self, button):
        if self.handle and self.game_view.player.action_handler.current_action is None:
            if button == 1 and self.first_pending.can_complete():
                self.game_view.turn_handler.current_handler.current_action = self.first_pending
                self.find_actions(self.game_view.window.mouse.e_x, self.game_view.window.mouse.e_y)
            elif button == 4 and self.second_pending.can_complete():
                self.game_view.turn_handler.current_handler.current_action = self.second_pending
                self.find_actions(self.game_view.window.mouse.e_x, self.game_view.window.mouse.e_y)

            if not self.game_view.player.action_handler.initiative:
                self.recheck = True

    def on_scroll(self, direction):
        if self.handle and self.game_view.player.action_handler.current_action is None:
            self.current_set = int(self.current_set + 2*direction)
            if self.current_set < 0:
                self.current_set = len(self.actions)-2
            else:
                self.current_set %= len(self.actions)
            self.set_actions()

    def set_actions(self):
        self.first_action = ACTION_WORDS.get(self.actions_ordered[self.current_set], None)
        action = self.actions_ordered[self.current_set]
        self.first_pending = turn.ACTIONS.get(action, turn.Action)(self.actions[action],
                                                                   self.game_view.turn_handler.current_handler)
        if self.first_pending.can_complete():
            self.first_action.alpha = 255
        else:
            self.first_action.alpha = 155

        self.second_action = ACTION_WORDS.get(self.actions_ordered[self.current_set+1], None)
        action = self.actions_ordered[self.current_set + 1]
        self.second_pending = turn.ACTIONS.get(action, turn.Action)(self.actions[action],
                                                                    self.game_view.turn_handler.current_handler)
        if self.second_pending.can_complete():
            self.second_action.alpha = 255
        else:
            self.second_action.alpha = 155


class TalkTab(Tab):

    def __init__(self, game_view):
        button_data = ({"x": 440, "y": 140,
                        "action": TriggerSimpleEventAction((self.end_convo,)),
                        'secondary': TriggerSimpleEventAction((self.go_rel_pos,)),
                        'texture': arcade.load_texture("assets/ui/ui_pieces.png", x=0, width=230, height=90)},
                       {"x": -390, "y": -140,
                        "action": TriggerSimpleEventAction((self.back,)),
                        'texture': arcade.load_texture("assets/ui/ui_pieces.png", x=0, y=270, width=230, height=90)},
                       {"x": -225, "y": -140,
                        "action": TriggerSimpleEventAction((self.next,)),
                        'texture': arcade.load_texture("assets/ui/ui_pieces.png", x=230, y=270, width=230, height=90)},
                       )
        super().__init__(arcade.load_texture("assets/ui/ui_split.png", x=2060, width=1030, height=650),
                         c.round_to_x(c.SCREEN_WIDTH // 2, 5 * c.SPRITE_SCALE),
                         c.round_to_x(c.SCREEN_HEIGHT // 2, 5 * c.SPRITE_SCALE), game_view, button_data=button_data)

        self.convo: interaction.Node = game_view.convo_handler
        self.current_node: interaction.Node = None
        self.node_buttons = []
        self.node_button_text = []
        self.convo_done = False
        self.next_node(self.convo)

    def load_convo(self, convo):
        self.convo = convo
        self.current_node = convo

        if isinstance(self.current_node.target, list):
            for target in self.current_node.target:
                self.game_view.map_handler.toggle_target_sprites(target)
        elif self.current_node.target >= 0:
            self.game_view.map_handler.toggle_target_sprites(self.current_node.target)

        self.strip_buttons(self.node_buttons)
        self.node_buttons = []
        self.node_button_text = []
        self.convo_done = False

        ShowTabAction((self, self.game_view.ui_elements)).act()

        self.find_node_buttons()

    def end_convo(self):
        if self.current_node is not None:
            self.current_node.reset()

        self.strip_buttons(self.node_buttons)
        self.node_buttons = []
        self.node_button_text = []

        self.convo_done = True

    def next_node(self, node):
        if self.current_node is not None:
            self.current_node.reset()
        self.current_node = node
        if isinstance(self.current_node.target, list):
            for target in self.current_node.target:
                self.game_view.map_handler.toggle_target_sprites(target)
        elif self.current_node.target >= 0:
            self.game_view.map_handler.toggle_target_sprites(self.current_node.target)
        self.current_node.reset()
        self.find_node_buttons()

    def find_node_buttons(self):
        self.strip_buttons(self.node_buttons)
        node_buttons = []
        button_text = []
        for index, key_node in enumerate(self.current_node.inputs.items()):
            button = {"x": -360, "y": 120 - 80 * index,
                      "action": TriggerSimpleEventAction((self.next_node, key_node[1])),
                      'texture': arcade.load_texture("assets/ui/ui_pieces.png", x=460, y=270, width=230, height=90)}
            button_text.append([key_node[0], button['x']-102, button['y']+39])
            node_buttons.append(button)
        self.node_button_text = button_text
        self.node_buttons = node_buttons

    def draw(self):
        if self.convo_done:
            HideTabAction((self, self.game_view.ui_elements)).act()
        else:
            super().draw()
            self.current_node.draw(self.center_x, self.center_y)
            # TODO: Create a proper text system and integrate into displays. Then remove this placeholder system.
            if len(self.node_buttons) and self.node_buttons[0] in self.button_data:
                for text in self.node_button_text:
                    arcade.draw_text(text[0],
                                     self.center_x + text[1] * c.SPRITE_SCALE,
                                     self.center_y + text[2] * c.SPRITE_SCALE,
                                     arcade.color.WHITE, anchor_y='top')

    def next(self):
        if self.current_node.forward_step():
            if len(self.node_buttons):
                self.load_buttons(self.node_buttons)
            else:
                self.convo_done = True

    def back(self):
        if self.current_node.backward_step():
            if isinstance(self.current_node.current_display, puzzle.TextPuzzle):
                self.convo_done = True
            if len(self.node_buttons):
                self.strip_buttons(self.node_buttons)

    def on_press(self, point):
        super().on_press(point)

    def on_key_press(self, key, modifier):
        self.current_node.on_key_press(key, modifier)

