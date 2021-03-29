import arcade
import constants as c
import isometric


class TemporumWindow(arcade.Window):
    """
    The Game Window, This holds the view and any constant variables as this will always be the same object.
    """

    def __init__(self):
        super().__init__(c.SCREEN_WIDTH, c.SCREEN_HEIGHT, c.WINDOW_NAME, fullscreen=c.FULLSCREEN)
        # The Views
        self.game = GameView()
        self.title = TitleView()

        # Always start with the title
        self.show_view(self.title)

    def on_key_press(self, symbol: int, modifiers: int):
        # At all times the ESCAPE key will close the game.
        if symbol == arcade.key.ESCAPE:
            self.close()


class GameView(arcade.View):
    """
    The GameView is the real game, it is where the gameplay will take place.
    """

    def __init__(self):
        super().__init__()
        # The tile lists.
        self.ground_tiles = isometric.IsoList()

    def on_draw(self):
        arcade.start_render()
        self.ground_tiles.draw()


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
