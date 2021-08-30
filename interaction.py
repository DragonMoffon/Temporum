import json

import arcade
from typing import Dict, List, Tuple

import constants as c
import puzzle

# All of the conversations
CONVERSATIONS = json.load(open("data/conversations.json"))
# All possible characters
characters = ['note', 'terminal', 'machine', 'computer', 'player']
# the speaker sprites.
SPEAKERS = {character: arcade.load_texture("assets/interaction/portraits.png", y=265+(265*index),
                                           width=280, height=265)
            for index, character in enumerate(characters)}


class DisplayText:

    def __init__(self, pages: list, page_events: dict, speaker: arcade.Sprite):
        """
        holds the text data for one of the speakers. either initiate or response. is a terrible and under used
        system that I would replace if I had time.
        :param pages: a list of strings.
        :param page_events: what happens on each page. If the page should shake or not. NOT USED
        :param speaker: the speaker sprite to show.
        """
        self.pages = pages
        self.speaker = speaker
        self.page_events = page_events
        self.current_page = -1
        self.current_event = None
        self.events = {None: self.display}
        self.cycle_step()

    def reset(self):
        # resets to the start.
        self.current_page = -1
        self.current_event = None
        self.cycle_step()

    def cycle_step(self):
        # This goes through the pages. If an event is running then stop it. If the event is done then go to next one.
        if self.current_event is not None:
            self.push_event()
            return False
        else:
            self.current_page += 1
            if self.current_page < len(self.pages):
                if self.current_page in self.page_events:
                    self.current_event = self.page_events[self.current_page]
                return False
        return True

    def back_step(self):
        # does the opposite of cycle step.
        self.current_page -= 1
        if self.current_page >= 0:
            self.current_event = None
            return False
        self.current_page = 0
        return True

    def push_event(self):
        # stop the event.
        self.current_event = None

    def key_input(self, key, modifier):
        # used by puzzles but is needed here so it doesn't crash
        pass

    def draw(self, x, y):
        # draw based on the current even.
        if self.current_page < len(self.pages):
            # This error doesn't make sense with my current knowledge
            self.events[self.current_event](*(x, y))

    def display(self, x: float, y: float):
        # draw the text and the speaker.
        arcade.draw_text(self.pages[self.current_page], x-465*c.SPRITE_SCALE, y+155*c.SPRITE_SCALE,
                         arcade.color.WHITE, anchor_y='top')
        self.speaker.center_x = c.round_to_x(x + 255*c.SPRITE_SCALE, 5*c.SPRITE_SCALE)
        self.speaker.center_y = c.round_to_x(y + 40*c.SPRITE_SCALE, 5*c.SPRITE_SCALE)
        self.speaker.draw()


class Node:

    def __init__(self, initiate, response, inputs, target):
        """
        A node is point in a conversation tree. It holds the data for what the initiate says, the response says, and
        has the next possible nodes in the conversation. It also holds the target for toggles.
        :param initiate: the display text for what the initiate says
        :param response: the display text for what the response says
        :param inputs: the next nodes in the conversation tree
        :param target: the target for toggling an iso sprite.
        """
        self.initiate_text: DisplayText = initiate
        self.response_text: DisplayText = response
        self.inputs: Dict[str, Node] = inputs
        self.steps = {self.initiate_text: self.response_text, self.response_text: self.inputs}
        self.current_display = self.initiate_text
        self.action: str = ''
        self.target: int = target

    def reset(self):
        # resets the node.
        self.current_display = self.initiate_text
        self.current_display.reset()

    def draw(self, x, y):
        # Draws the current display
        if isinstance(self.current_display, DisplayText) or isinstance(self.current_display, puzzle.TextPuzzle):
            self.current_display.draw(x, y)
        else:
            pass

    def on_key_press(self, key, modifier):
        # gives the current display the key inputs/
        if self.current_display is not self.inputs:
            self.current_display.key_input(key, modifier)

    def forward_step(self):
        # moves to the next display
        if isinstance(self.current_display, DisplayText) or isinstance(self.current_display, puzzle.TextPuzzle):
            # if it is a puzzle or a display text then check cycle through, and only if the display/puzzle is done
            # can the next step be done.
            if self.current_display.cycle_step():
                # go to next display
                self.current_display = self.steps[self.current_display]

                # if the display text has no pages then skip it
                if isinstance(self.current_display, DisplayText) and not len(self.current_display.pages):
                    self.forward_step()
                if isinstance(self.current_display, dict):
                    return True
                else:
                    self.current_display.reset()
        return False

    def backward_step(self):
        # opposite of forward step.
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
    """
    Loads the conversation and converts it to nodes.
    :param conversation: the conversation to load
    :return: the first conversation node.
    """

    # all the nodes that loop. These have to be done afterwards
    loop_data: List[Tuple[(str, str, str)]] = []

    # the default speaker so not all the conversation nodes have to store the speaker info.
    default_speaker: List[str, str] = None

    def load_loop(convo):
        """
        goes through the loop data and connects all the nodes.
        :param convo: the starting node of the conversation.
        """
        def find_node(loop):
            """
            use the loop info to find the node to connect to.
            :param loop: the key chain to find the base node.
            :return: the input node needed and it's location.
            """
            location = loop.split("_")
            next_node = convo
            for node in location:
                if node in next_node.inputs:
                    next_node = next_node.inputs[node]
            return next_node, location[-1]

        for node_loop in loop_data:
            # find the target node and the base node then connect them together.
            target_node, target_location = find_node(node_loop[0])
            loop_node, loop_location = find_node(node_loop[1])
            if node_loop[-1].strip('_') != "":
                target_location = node_loop[-1]
            loop_node.inputs[target_location] = target_node

        return convo

    def load_display(display_data, speaker):
        if 'puzzle_' in display_data:
            # If the display text is a puzzle then make a puzzle.
            speaker_sprite = arcade.Sprite(scale=c.SPRITE_SCALE)
            speaker_sprite.texture = SPEAKERS[speaker]

            return puzzle.TextPuzzle(display_data.split('_')[-1], speaker_sprite)
        else:
            # If the display has text then make a DisplayText object
            speaker_sprite = arcade.Sprite(scale=c.SPRITE_SCALE)
            speaker_sprite.texture = SPEAKERS[speaker]
            if isinstance(display_data, str):
                display: DisplayText = DisplayText([display_data], {0: None}, speaker_sprite)
            else:
                display: DisplayText = DisplayText(display_data, {0: None}, speaker_sprite)
            return display

    def load_node(node_data, location=''):
        """
        This is a recurring function that goes depth first into the conversation tree.
        :param node_data: all the data for the node to load and the next nodes
        :param location: it's chain of input keys.
        :return: the created node.
        """

        nonlocal default_speaker

        # set the default speaker.
        default_speaker = node_data.get("default", default_speaker)
        if default_speaker is None:
            default_speaker = node_data.get("speakers", default_speaker)

        # set the speaker.
        speakers = node_data.get('speakers', default_speaker)

        # load teh initiate and response displays.
        initiate = load_display(node_data['initiate'], speakers[0])
        response = load_display(node_data['response'], speakers[1])

        # set the target if here is one.
        target = node_data.get('target', -1)

        # Create all the input nodes. This is where the function is called again.
        inputs = {}
        for key, next_node in node_data['inputs'].items():
            if isinstance(next_node, str):
                loop_data.append((next_node, f"{location}{key}", key))
            else:
                inputs[key] = load_node(next_node, f"{location}{key}_")

        # return the created node.
        return Node(initiate, response, inputs, target)

    # the data.
    data = CONVERSATIONS[conversation]

    # the conversation node.
    conversation_node = load_node(data)

    # return the final node after finding the loop nodes..
    return load_loop(conversation_node)
