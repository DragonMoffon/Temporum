import json

import arcade
from typing import Dict, List, Tuple

import constants as c
import puzzle

CONVERSATIONS = json.load(open("data/conversations.json"))
characters = ['note', 'terminal', 'machine', 'computer', 'player']
SPEAKERS = {character: arcade.load_texture("assets/interaction/portraits.png", y=265+(265*index),
                                           width=280, height=265)
            for index, character in enumerate(characters)}


class DisplayText:

    def __init__(self, pages: list, page_events: dict, speaker: arcade.Sprite):
        self.pages = pages
        self.speaker = speaker
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
            elif self.current_page in self.page_events:
                self.current_event = self.page_events[self.current_page]
            return False
        return True

    def back_step(self):
        self.current_page -= 1
        if self.current_page >= 0:
            self.current_event = None
            return False
        self.current_page = 0
        return True

    def push_event(self):
        self.current_event = None

    def key_input(self, key, modifier):
        pass

    def draw(self, x, y):
        if self.current_page < len(self.pages):
            # This error doesn't make sense with my current knowledge
            self.events[self.current_event](*(x, y))

    def display(self, x: float, y: float):
        arcade.draw_text(self.pages[self.current_page], x-465*c.SPRITE_SCALE, y+155*c.SPRITE_SCALE,
                         arcade.color.WHITE, anchor_y='top')
        self.speaker.center_x = c.round_to_x(x + 255*c.SPRITE_SCALE, 5*c.SPRITE_SCALE)
        self.speaker.center_y = c.round_to_x(y + 40*c.SPRITE_SCALE, 5*c.SPRITE_SCALE)
        self.speaker.draw()


class Node:

    def __init__(self, initiate, response, inputs, target):
        self.initiate_text: DisplayText = initiate
        self.response_text: DisplayText = response
        self.inputs: Dict[str, Node] = inputs
        self.steps = {self.initiate_text: self.response_text, self.response_text: self.inputs}
        self.current_display = self.initiate_text
        self.action: str = ''
        self.target: int = target

    def reset(self):
        self.current_display = self.initiate_text
        self.current_display.reset()

    def draw(self, x, y):
        if isinstance(self.current_display, DisplayText) or isinstance(self.current_display, puzzle.TextPuzzle):
            self.current_display.draw(x, y)
        else:
            pass

    def on_key_press(self, key, modifier):
        if self.current_display is not self.inputs:
            self.current_display.key_input(key, modifier)

    def forward_step(self):
        if isinstance(self.current_display, DisplayText) or isinstance(self.current_display, puzzle.TextPuzzle):
            if self.current_display.cycle_step():
                self.current_display = self.steps[self.current_display]
                if isinstance(self.current_display, DisplayText) and not len(self.current_display.pages):
                    self.forward_step()
                if isinstance(self.current_display, dict):
                    return True
                else:
                    self.current_display.reset()
        return False

    def backward_step(self):
        if isinstance(self.current_display, DisplayText):
            if self.current_display.back_step():
                self.current_display = self.initiate_text
                self.current_display.back_step()
            return False
        elif isinstance(self.current_display, dict):
            self.current_display = self.response_text
            if not len(self.current_display.pages):
                self.current_display = self.initiate_text
            self.current_display.back_step()
        return True


def load_conversation(conversation="tutorial_start"):
    loop_data: List[Tuple[(str, str, str)]] = []
    default_speaker: List[str, str] = None

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
            if node_loop[-1].strip('_') != "":
                target_location = node_loop[-1]
            loop_node.inputs[target_location] = target_node

        return convo

    def load_display(display_data, speaker):
        if 'puzzle_' in display_data:
            speaker_sprite = arcade.Sprite(scale=c.SPRITE_SCALE)
            speaker_sprite.texture = SPEAKERS[speaker]

            return puzzle.TextPuzzle(display_data.split('_')[-1], speaker_sprite)
        else:
            speaker_sprite = arcade.Sprite(scale=c.SPRITE_SCALE)
            speaker_sprite.texture = SPEAKERS[speaker]
            if isinstance(display_data, str):
                display: DisplayText = DisplayText([display_data], {0: None}, speaker_sprite)
            else:
                display: DisplayText = DisplayText(display_data, {0: None}, speaker_sprite)
            return display

    def load_node(node_data, location=''):
        nonlocal default_speaker
        default_speaker = node_data.get("default", default_speaker)
        if default_speaker is None:
            default_speaker = node_data.get("speakers", default_speaker)
        speakers = node_data.get('speakers', default_speaker)

        initiate = load_display(node_data['initiate'], speakers[0])
        response = load_display(node_data['response'], speakers[1])

        target = node_data.get('target', -1)

        inputs = {}
        for key, next_node in node_data['inputs'].items():
            if isinstance(next_node, str):
                loop_data.append((next_node, f"{location}{key}", key))
            else:
                inputs[key] = load_node(next_node, f"{location}{key}_")

        return Node(initiate, response, inputs, target)

    data = CONVERSATIONS[conversation]

    conversation_node = load_node(data)
    return load_loop(conversation_node)
