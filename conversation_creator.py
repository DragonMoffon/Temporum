import json
import math

import arcade


def backspace(string):
    return string[:-1]


def space(string):
    return string + " "


keys = {arcade.key.A: "a",
        arcade.key.B: "b",
        arcade.key.C: "c",
        arcade.key.D: "d",
        arcade.key.E: "e",
        arcade.key.F: "f",
        arcade.key.G: "g",
        arcade.key.H: "h",
        arcade.key.I: "i",
        arcade.key.J: "j",
        arcade.key.K: "k",
        arcade.key.L: "l",
        arcade.key.M: "m",
        arcade.key.N: "n",
        arcade.key.O: "o",
        arcade.key.P: "p",
        arcade.key.Q: "q",
        arcade.key.R: "r",
        arcade.key.S: "s",
        arcade.key.T: "t",
        arcade.key.U: "u",
        arcade.key.V: "v",
        arcade.key.W: "w",
        arcade.key.X: "x",
        arcade.key.Y: "y",
        arcade.key.Z: "z",
        arcade.key.COMMA: ",",
        arcade.key.PERIOD: ".",
        arcade.key.APOSTROPHE: '\''}

shift_keys = {arcade.key.A: "A",
              arcade.key.B: "B",
              arcade.key.C: "C",
              arcade.key.D: "D",
              arcade.key.E: "E",
              arcade.key.F: "F",
              arcade.key.G: "G",
              arcade.key.H: "H",
              arcade.key.I: "I",
              arcade.key.J: "J",
              arcade.key.K: "K",
              arcade.key.L: "L",
              arcade.key.M: "M",
              arcade.key.N: "N",
              arcade.key.O: "O",
              arcade.key.P: "P",
              arcade.key.Q: "Q",
              arcade.key.R: "R",
              arcade.key.S: "S",
              arcade.key.T: "T",
              arcade.key.U: "U",
              arcade.key.V: "V",
              arcade.key.W: "W",
              arcade.key.X: "X",
              arcade.key.Y: "Y",
              arcade.key.Z: "Z",
              arcade.key.SLASH: "?",
              arcade.key.KEY_1: "!",
              arcade.key.APOSTROPHE: '\"',
              arcade.key.ENTER: "\n"}

function_keys = {arcade.key.BACKSPACE: backspace, arcade.key.SPACE: space}


class Event(arcade.SpriteSolidColor):

    def __init__(self, x, y, text, inputs):
        super().__init__(150, 50, arcade.color.WHITE)
        self.center_x = x
        self.center_y = y
        self.text = text
        self.text = {"expressed": text, "initiate": "", "response": ""}
        self.next_inputs = []
        self.inputs = inputs

    def draw_hit_box(self, color: arcade.Color = arcade.color.BLACK, line_thickness: float = 1):
        arcade.draw_text(self.text['expressed'], self.center_x, self.center_y + 25,
                         color, anchor_x='center', anchor_y="top")

    def move(self, new_pos):
        self.center_x += new_pos[0]
        self.center_y += new_pos[1]
        for inputs in self.next_inputs:
            inputs.place_start((self.center_x, self.center_y-25))

        if self.inputs is not None:
            for inputs in self.inputs:
                inputs.place_end((self.center_x, self.center_y+25))

    def tab_draw(self, tab):
        input_text = ""
        for inputs in self.inputs:
            input_text += f"{inputs.text['expressed']}\n"

        arcade.draw_text(input_text, tab.center_x - 230, tab.center_y + 165,
                         arcade.color.BLACK, 15, anchor_y="top")

        output_text = ""
        for outputs in self.next_inputs:
            output_text += f"{outputs.text['expressed']}\n"

        arcade.draw_text(output_text, tab.center_x - 230, tab.center_y - 85,
                         arcade.color.BLACK, 15, anchor_y="top")

        arcade.draw_text(self.text['initiate'], tab.center_x + 5, tab.center_y + 165,
                         arcade.color.BLACK, 15, anchor_y="top")

        arcade.draw_text(self.text['response'], tab.center_x + 5, tab.center_y - 85,
                         arcade.color.BLACK, 15, anchor_y="top")


class InitiateJoint(arcade.SpriteSolidColor):

    def __init__(self, s_x, s_y, e_x, e_y, text, from_event, loop=False):
        super().__init__(100, 25, arcade.color.WHITE)
        self.start_point = (s_x, s_y)
        self.end_point = (e_x, e_y)
        self.place_end((e_x, e_y))
        self.text = {'expressed': text}
        self.from_event = from_event
        self.next = None
        self.loop = loop

    def draw_hit_box(self, color: arcade.Color = arcade.color.BLACK, line_thickness: float = 1):
        arcade.draw_line(self.start_point[0], self.start_point[1],
                         self.end_point[0], self.end_point[1],
                         arcade.color.WHITE)
        direction = self.start_point[0] - self.end_point[0], self.start_point[1] - self.end_point[1]
        length = math.sqrt(direction[0]**2 + direction[1]**2)
        direction = direction[0]/length, direction[1]/length
        arcade.draw_triangle_filled(self.end_point[0]+direction[0]*25, self.end_point[1]+direction[1]*25,
                                    self.end_point[0] + direction[0]*45 - direction[1] * 35,
                                    self.end_point[1] + direction[1]*45 + direction[0] * 35,
                                    self.end_point[0] + direction[0]*45 + direction[1] * 35,
                                    self.end_point[1] + direction[1]*45 - direction[0] * 35,
                                    arcade.color.WHITE)
        arcade.draw_text(self.text['expressed'], self.center_x, self.center_y + 15,
                         color, anchor_y="top", anchor_x='center')

    def place_end(self, end_pos):
        self.end_point = end_pos
        center = ((end_pos[0]+self.start_point[0])/2 + 50, (end_pos[1]+self.start_point[1])/2)
        self.center_x, self.center_y = center

    def place_start(self, start_pos):
        self.start_point = start_pos
        center = ((start_pos[0]+self.end_point[0])/2 + 50, (start_pos[1]+self.end_point[1])/2)
        self.center_x, self.center_y = center

    def tab_draw(self, tab):
        arcade.draw_text(self.text['expressed'], tab.center_x+15, tab.center_y+75, arcade.color.BLACK, 15)


TEXTURES = {Event: arcade.load_texture("assets/tools/convocreatortab.png", width=480, height=567),
            InitiateJoint: arcade.load_texture("assets/tools/convocreatortab.png", x=480, width=480, height=567)}


class ConvoWindow(arcade.Window):

    def __init__(self):
        super().__init__(1000, 1000, "CONVO CREATOR!", fullscreen=True)
        self.center_window()
        self.view_x = 0
        self.view_y = 0

        self.data = {}

        self.convo_name_tab = arcade.Sprite("assets/tools/convocreatortab.png",
                                            center_x=self.width / 2, center_y=self.height / 2,
                                            image_width=480, image_height=567, image_x=960)
        self.tab = arcade.Sprite("assets/tools/convocreatortab.png", image_width=480, image_height=567,
                                 center_x=self.width - 120, center_y=self.height / 2)
        self.text_tab = arcade.Sprite("assets/tools/convocreatortext.png", center_x=320, center_y=self.height / 2)

        self.segment_list = arcade.SpriteList()
        self.start = Event(self.width/2, self.height-200, "Start", [])
        self.segment_list.append(self.start)
        self.selected_segment = None
        self.current_text = ""
        self.convo_name = None
        self.current_text_location = ""
        self.segment_texts = {}
        self.new_joint = None
        self.dragging = False

    def place_tab(self):
        self.tab.texture = TEXTURES[type(self.current_segment)]
        self.tab.center_x = self.view_x + self.width - self.tab.width/2
        self.tab.center_y = self.view_y + self.height/2

    def on_draw(self):
        arcade.start_render()
        self.segment_list.draw()
        self.segment_list.draw_hit_boxes()
        if self.current_segment is not None:
            self.tab.draw()
            self.current_segment.tab_draw(self.tab)

        if self.current_text is not None:
            if self.convo_name is None:
                self.convo_name_tab.draw()
                arcade.draw_text(self.current_text, self.convo_name_tab.center_x, self.text_tab.center_y+175,
                                 arcade.color.BLACK, anchor_y='top', anchor_x='center', font_size=35)
            else:
                self.text_tab.draw()
                arcade.draw_text(self.current_text, self.text_tab.center_x-60, self.text_tab.center_y+75,
                                 arcade.color.BLACK, anchor_y='top')
                segment_texts = ""
                for key, value in self.segment_texts.items():
                    segment_texts += f"{key+1}: {value}\n"

                arcade.draw_text(segment_texts, self.text_tab.center_x-200, self.text_tab.center_y+45,
                                 arcade.color.BLACK, anchor_y='top')

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.ESCAPE:
            self.close()
        elif symbol == arcade.key.S and modifiers & arcade.key.MOD_CTRL:
            if isinstance(self.current_text, str):
                self.apply_text()
            self.save_to_json()
        elif isinstance(self.current_text, str):
            if modifiers & arcade.key.MOD_CTRL and arcade.key.KEY_1 <= symbol <= arcade.key.KEY_9:
                self.switch_text(symbol - arcade.key.KEY_1)
            elif symbol in function_keys:
                self.current_text = function_keys[symbol](self.current_text)
            elif modifiers & arcade.key.MOD_SHIFT or modifiers & arcade.key.MOD_CAPSLOCK:
                if symbol in shift_keys:
                    self.current_text += shift_keys[symbol]
            elif symbol in keys:
                self.current_text += keys[symbol]
            elif symbol == arcade.key.ENTER:
                self.apply_text()

    def apply_text(self):
        if isinstance(self.current_text, str):
            if self.convo_name is None:
                self.convo_name = self.current_text
                self.current_text = None
            else:
                self.current_segment.text[self.current_text_location] = self.current_text
                self.current_text = None
                self.current_text_location = ''

    def get_text(self):
        self.segment_texts = {x: k for x, k in enumerate(self.current_segment.text)}
        self.current_text_location = 'expressed'
        self.current_text = self.current_segment.text[self.current_text_location]

    def switch_text(self, number):
        if number in self.segment_texts:
            self.apply_text()
            self.current_text_location = self.segment_texts[number]
            self.current_text = self.current_segment.text[self.current_text_location]

    def check_segment_collision(self, x, y):
        collided = None
        self.dragging = False
        for segment in self.segment_list:
            if segment.collides_with_point((self.view_x + x, self.view_y + y)):
                collided = segment
                break
        return collided

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        collided = self.check_segment_collision(x, y)

        if button == 1:
            self.current_segment = collided
            if collided is not None:
                self.place_tab()
                if isinstance(collided, Event):
                    self.dragging = True

        elif button == 4:
            self.current_segment = collided
            if collided is not None and isinstance(collided, Event):

                self.new_joint = InitiateJoint(collided.center_x, collided.center_y-25,
                                               self.view_x+x, self.view_y+y, str(len(collided.next_inputs)),
                                               collided)
                collided.next_inputs.append(self.new_joint)
                self.segment_list.append(self.new_joint)

    def on_mouse_release(self, x: float, y: float, button: int,
                         modifiers: int):
        self.dragging = False
        if self.new_joint is not None:
            collided = self.check_segment_collision(x, y)
            self.current_segment = self.new_joint
            if isinstance(collided, Event):
                self.new_joint.next = collided
                collided.inputs.append(self.new_joint)
                self.new_joint.loop = True
            else:
                event = Event(self.view_x + x, self.view_y + y - 25,
                              str(self.new_joint.text['expressed']), [self.new_joint])
                self.segment_list.append(event)
                self.new_joint.next = event
            self.dragging = False
            self.new_joint = None

    def on_mouse_drag(self, x: float, y: float, dx: float, dy: float, buttons: int, modifiers: int):
        if self.dragging and self.current_segment is not None:
            self.current_segment.move((dx, dy))
        elif buttons == 2:
            self.view_x -= dx
            self.view_y -= dy
            self.tab.center_x -= dx
            self.tab.center_y -= dy
            self.text_tab.center_x -= dx
            self.text_tab.center_y -= dy
            self.set_viewport(self.view_x, self.view_x + self.width, self.view_y, self.view_y + self.height)
        elif buttons == 4:
            if self.new_joint is not None:
                self.new_joint.place_end((self.view_x+x, self.view_y+y))

    @property
    def current_segment(self):
        return self.selected_segment

    @current_segment.setter
    def current_segment(self, value):
        if value is not None:
            self.selected_segment = value
            self.place_tab()
            self.get_text()
        else:
            self.apply_text()
            self.selected_segment = value

    def find_location(self, node, location=None):
        if len(node.inputs) and node.inputs[0] is not None:
            if location is None:
                location = node.inputs[0].text['expressed']
            else:
                location = f"{node.inputs[0].text['expressed']}_{location}"
            prev = node.inputs[0].from_event
            return self.find_location(prev, location)
        return location

    def delve_node(self, node):
        data = {"initiate": node.text['initiate'], "response": node.text['response'], "inputs": {}}
        for x in node.next_inputs:
            if x.loop:
                data['inputs'][x.text['expressed']] = self.find_location(x.next)
            else:
                data['inputs'][x.text['expressed']] = self.delve_node(x.next)
        return data

    def save_to_json(self):
        self.data = self.delve_node(self.start)
        with open(f"data/{self.convo_name}.json", "w") as save_file:
            json.dump(self.data, save_file, indent=4)

    def load_from_json(self):
        pass


def main():
    window = ConvoWindow()
    arcade.run()


if __name__ == '__main__':
    main()
