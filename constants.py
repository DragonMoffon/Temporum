import arcade

# Isometric Sprite Data
TILE_WIDTH, TILE_HEIGHT = 160, 80
SPRITE_SCALE = 0.6
FLOOR_TILE_THICKNESS = 20

# Window Information
SCREEN_WIDTH, SCREEN_HEIGHT = arcade.get_display_size()
WINDOW_NAME, FULLSCREEN = "Temporum: The Melclex Incident", True

# Movement dictionary
DIRECTIONS = {arcade.key.UP: 0, arcade.key.RIGHT: 1,
              arcade.key.DOWN: 2, arcade.key.LEFT: 3}
