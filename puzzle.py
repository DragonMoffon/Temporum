import time
from dataclasses import dataclass

import arcade
from typing import Tuple

import constants as c

keys = {
    arcade.key.A: "a",
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
    arcade.key.KEY_1: "1",
    arcade.key.KEY_2: "2",
    arcade.key.KEY_3: "3",
    arcade.key.KEY_4: "4",
    arcade.key.KEY_5: "5",
    arcade.key.KEY_6: "6",
    arcade.key.KEY_7: "7",
    arcade.key.KEY_8: "8",
    arcade.key.KEY_9: "9",
    arcade.key.KEY_0: "0"
}
shift_keys = {
    arcade.key.A: "A",
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
    arcade.key.KEY_1: "!",
    arcade.key.KEY_2: "@",
    arcade.key.KEY_3: "#",
    arcade.key.KEY_4: "$",
    arcade.key.KEY_5: "%",
    arcade.key.KEY_6: "^",
    arcade.key.KEY_7: "&",
    arcade.key.KEY_8: "*",
    arcade.key.KEY_9: "(",
    arcade.key.KEY_0: ")"}


@dataclass()
class TextBox:
    rel_pos: Tuple[int, int]
    sprite: arcade.Sprite
    letter: str = ""


class TextPuzzle:

    def __init__(self, puzzle_answer, speaker):
        self.answer = puzzle_answer
        self.input = ""
        self.complete = False

        self.speaker = speaker

        self.shake = False
        self.text_boxes = arcade.SpriteList()
        self.letters = []
        start = c.round_to_x(- 450 * c.SPRITE_SCALE, 5 * c.SPRITE_SCALE)
        for x, char in enumerate(self.answer):
            sprite = arcade.Sprite("assets/ui/ui_pieces.png", c.SPRITE_SCALE, 460, 90, 230, 90)
            self.text_boxes.append(sprite)
            self.letters.append(TextBox((c.round_to_x(start + (50 * c.SPRITE_SCALE * x), 5 * c.SPRITE_SCALE),
                                         c.round_to_x(130 * c.SPRITE_SCALE, 5*c.SPRITE_SCALE)), sprite))

        self.shake_start = 0

    def key_input(self, key, modifier):
        if key == arcade.key.ENTER:
            if self.input == self.answer:
                self.complete = True
            else:
                self.shake = True
                self.shake_start = time.time()

        elif key == arcade.key.BACKSPACE:
            self.input = self.input[:-1]
            self.letters[len(self.input)].letter = ""
        elif key in keys and not self.shake:
            if modifier & arcade.key.LSHIFT:
                new_key = shift_keys[key]
            else:
                new_key = keys[key]

            if len(self.input) < len(self.answer):
                self.input += new_key
                self.letters[len(self.input)-1].letter = new_key

    def reset(self):
        if not self.complete:
            self.input = ""
            for letter in self.letters:
                letter.letter = ""

    def cycle_step(self):
        if self.complete:
            return True
        return False

    def draw(self, x, y):
        if self.complete:
            color = arcade.color.GREEN
        elif self.shake:
            color = arcade.color.RED
            if self.shake_start + 1/2 < time.time():
                self.shake = False
                self.shake_start = 0
                self.input = ""
                for letter in self.letters:
                    letter.letter = ""

        else:
            color = arcade.color.WHITE

        for letter in self.letters:
            letter.sprite.center_x = x + letter.rel_pos[0]
            letter.sprite.center_y = y + letter.rel_pos[1]
            letter.sprite.draw()
            arcade.draw_text(letter.letter, letter.sprite.center_x, letter.sprite.center_y, color,
                             anchor_x='center', anchor_y='center', font_size=16)

        self.speaker.center_x = c.round_to_x(x + 255 * c.SPRITE_SCALE, 5 * c.SPRITE_SCALE)
        self.speaker.center_y = c.round_to_x(y + 40 * c.SPRITE_SCALE, 5 * c.SPRITE_SCALE)
        self.speaker.draw()
