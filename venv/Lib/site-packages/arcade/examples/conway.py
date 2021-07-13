"""
Conway's Game of Life
python -m arcade.examples.conway
"""
import arcade
import random

# Set how many rows and columns we will have
ROW_COUNT = 70
COLUMN_COUNT = 150

# This sets the WIDTH and HEIGHT of each grid location
WIDTH = 15
HEIGHT = 15

# This sets the margin between each cell
# and on the edges of the screen.
MARGIN = 0

# Do the math to figure out our screen dimensions
SCREEN_WIDTH = (WIDTH + MARGIN) * COLUMN_COUNT + MARGIN
SCREEN_HEIGHT = (HEIGHT + MARGIN) * ROW_COUNT + MARGIN
SCREEN_TITLE = "Conway's Game of Life"

ALIVE_COLOR = arcade.color.BISTRE
DEAD_COLOR = arcade.color.WHITE
BACKGROUND_COLOR = arcade.color.ANTIQUE_WHITE

def create_grids(width, height):
    # One dimensional list of all sprites in the two-dimensional sprite list
    grid_sprites_one_dim = arcade.SpriteList()

    # This will be a two-dimensional grid of sprites to mirror the two
    # dimensional grid of numbers. This points to the SAME sprites that are
    # in grid_sprite_list, just in a 2d manner.
    grid_sprites_two_dim = []

    # Create a list of solid-color sprites to represent each grid location
    for row in range(ROW_COUNT):
        grid_sprites_two_dim.append([])
        for column in range(COLUMN_COUNT):
            x = column * (WIDTH + MARGIN) + (WIDTH / 2 + MARGIN)
            y = row * (HEIGHT + MARGIN) + (HEIGHT / 2 + MARGIN)
            sprite = arcade.SpriteCircle(WIDTH // 2, arcade.color.WHITE, soft=True)
            sprite.center_x = x
            sprite.center_y = y
            grid_sprites_one_dim.append(sprite)
            grid_sprites_two_dim[row].append(sprite)

    return grid_sprites_one_dim, grid_sprites_two_dim


def randomize_grid(grid):
    for cell in grid:
        pick = random.randrange(2)
        if pick:
            cell.color = ALIVE_COLOR
        else:
            cell.color = DEAD_COLOR


class MyGame(arcade.Window):
    """
    Main application class.
    """

    def __init__(self, width, height, title):
        """
        Set up the application.
        """
        super().__init__(width, height, title)

        arcade.set_background_color(BACKGROUND_COLOR)

        grid_sprites_one_dim1, grid_sprites_two_dim1 = create_grids(width, height)
        assert grid_sprites_one_dim1[0] is grid_sprites_two_dim1[0][0]
        grid_sprites_one_dim2, grid_sprites_two_dim2 = create_grids(width, height)

        self.layers_grid_sprites_one_dim = [grid_sprites_one_dim1, grid_sprites_one_dim2]
        self.layers_grid_sprites_two_dim = [grid_sprites_two_dim1, grid_sprites_two_dim2]

        self.cur_layer = 0
        randomize_grid(self.layers_grid_sprites_one_dim[0])

    def on_draw(self):
        """ Render the screen. """

        # This command has to happen before we start drawing
        arcade.start_render()
        self.layers_grid_sprites_one_dim[0].draw()
        self.layers_grid_sprites_one_dim[0].vbo_buf = None

    def on_update(self, delta_time):
        if self.cur_layer == 0:
            layer1 = self.layers_grid_sprites_two_dim[0]
            layer2 = self.layers_grid_sprites_two_dim[1]
            self.cur_layer = 1
        else:
            layer1 = self.layers_grid_sprites_two_dim[1]
            layer2 = self.layers_grid_sprites_two_dim[0]
            self.cur_layer = 0

        for row in range(ROW_COUNT):
            for column in range(COLUMN_COUNT):
                live_neighbors = 0
                # -1 -1
                if row > 0 and column > 0 and layer1[row - 1][column - 1].color == ALIVE_COLOR:
                    live_neighbors += 1
                # -1  0
                if row > 0 and layer1[row - 1][column].color == ALIVE_COLOR:
                    live_neighbors += 1
                # -1 +1
                if row > 0 and column < COLUMN_COUNT - 1 and layer1[row - 1][column + 1].color == ALIVE_COLOR:
                    live_neighbors += 1
                #  0 +1
                if column < COLUMN_COUNT - 1 and layer1[row][column + 1].color == ALIVE_COLOR:
                    live_neighbors += 1
                # +1 +1
                if row < ROW_COUNT - 1 and column < COLUMN_COUNT - 1 and layer1[row + 1][column + 1].color == ALIVE_COLOR:
                    live_neighbors += 1
                # +1  0
                if row < ROW_COUNT - 1 and layer1[row + 1][column].color == ALIVE_COLOR:
                    live_neighbors += 1
                # +1 -1
                if row < ROW_COUNT - 1 and column > 0 and layer1[row + 1][column - 1].color == ALIVE_COLOR:
                    live_neighbors += 1
                #  0 -1
                if column > 0 and layer1[row][column - 1].color == ALIVE_COLOR:
                        live_neighbors += 1

                if layer1[row][column].color == ALIVE_COLOR and (live_neighbors == 2 or live_neighbors == 3):
                    if layer2[row][column].color == DEAD_COLOR:
                        layer2[row][column].color = ALIVE_COLOR
                elif layer1[row][column].color == DEAD_COLOR and live_neighbors == 3:
                    if layer2[row][column].color == DEAD_COLOR:
                        layer2[row][column].color = ALIVE_COLOR
                else:
                    if layer2[row][column].color == ALIVE_COLOR:
                        layer2[row][column].color = DEAD_COLOR


        """
        Any live cell with two or three live neighbours survives.
        Any dead cell with three live neighbours becomes a live cell.
        All other live cells die in the next generation. Similarly, all other dead cells stay dead.
        """


def main():
    MyGame(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    arcade.run()


if __name__ == "__main__":
    main()
