import json

import arcade

import constants as c


class DisplayText:

    def __init__(self, pages: list, page_events: dict):
        self.pages = pages
        self.page_events = page_events
        self.current_page = -1
        self.current_event = None
        self.events = {None: self.display}
        self.cycle_step()

    def reset(self):
        self.current_page = -1
        self.current_event = None
        self.cycle_step()

    def cycle_step(self):
        self.current_page += 1
        if self.current_page < len(self.pages):
            if self.current_event is not None:
                self.push_event()
            else:
                if self.current_page in self.page_events:
                    self.current_event = self.page_events[self.current_page]
            return False
        return True

    def on_press(self):
        return self.cycle_step()

    def push_event(self):
        self.current_event = None

    def draw(self, x, y):
        self.events[self.current_event](x, y)

    def display(self, x, y):
        arcade.draw_text(self.pages[self.current_page], x-390*c.SPRITE_SCALE, y+50*c.SPRITE_SCALE,
                         arcade.color.WHITE, anchor_y='top')


class Node:

    def __init__(self, initiate, response, inputs):
        self.initiate_text: DisplayText = initiate
        self.response_text: DisplayText = response
        self.inputs: dict[str, Node] = inputs
        self.steps = {self.initiate_text: self.response_text, self.response_text: self.inputs}
        self.current_display = self.initiate_text

    def reset(self):
        self.current_display = self.initiate_text
        self.current_display.reset()

    def draw(self, x, y):
        if isinstance(self.current_display, DisplayText):
            self.current_display.draw(x, y)
        else:
            pass

    def on_press(self):
        if isinstance(self.current_display, DisplayText):
            if self.current_display.on_press():
                self.current_display = self.steps[self.current_display]
                if isinstance(self.current_display, dict):
                    return True
                else:
                    self.current_display.reset()
        return False


def load_conversation(conversation="data/Sample Conversation.json"):
    loop_data: list[tuple[(str, str)]] = []

    def load_loop(convo):
        def find_node(loop):
            location = loop.split("_")
            next_node = convo
            for node in location:
                if node in next_node.inputs:
                    next_node = next_node.inputs[node]
            return next_node, location[-1]

        for node_loop in loop_data:
            target_node, target_location = find_node(node_loop[0])
            loop_node, loop_location = find_node(node_loop[1])
            loop_node.inputs[target_location] = target_node

        return convo

    def load_display(display_data):
        display: DisplayText = DisplayText([display_data], {0: None})
        return display

    def load_node(node_data, location=''):
        initiate = load_display(node_data['initiate'])
        response = load_display(node_data['response'])
        inputs = {}
        for key, next_node in node_data['inputs'].items():
            if isinstance(next_node, str):
                loop_data.append((next_node, f"{location}{key}"))
            else:
                inputs[key] = load_node(next_node, f"{location}{key}_")

        return Node(initiate, response, inputs)

    with open(conversation) as convo_file:
        data = json.load(convo_file)

    conversation = load_node(data)
    return load_loop(conversation)

