import isometric
import turn
import constants as c


class SimpleMoveBot(isometric.IsoActor):
    """
    The Simple Move Bot is the simplest bot it simply moves to the closest tile with low priority. That's it.
    """

    def __init__(self, e_x, e_y, text, grid_2d):
        super().__init__(e_x, e_y, text[0], 6)
        self.textures = text
        self.set_grid(grid_2d)
        self.algorithm = 'target_player'

        # The shock timer is a small turn timer for when the bot is hit by the player.
        self.shock_timer = 0

        # If the bot should end it's turn early.
        self.end_turn = False

    def new_pos(self, e_x, e_y):
        super().new_pos(e_x, e_y)
        # This is so the bot will appear if they come into the FOV of the player.
        if not c.PLAYER.game_view.map_handler.map.check_seen((e_x, e_y)):
            c.iso_remove(self)
        else:
            c.iso_append(self)

    def update(self):
        # The tiny terrible decision tree.
        if self.action_handler.current_action is None and self.action_handler.initiative > 0:
            # If bot's turn and not currently doing something/
            if self.shock_timer:
                # If shocked. don't
                self.set_iso_texture(self.textures[1])
                self.shock_timer -= 1
                self.action_handler.pass_turn()
            elif self.end_turn:
                # end turn
                self.action_handler.current_action = turn.ACTIONS['end']([None], self.action_handler)
                self.end_turn = False
            else:
                # choose the best place to move to. Then move there.
                self.set_iso_texture(self.textures[0])
                move_node = c.PLAYER.game_view.map_handler.full_map[c.PLAYER.e_x, c.PLAYER.e_y]
                self.action_handler.current_action = turn.ACTIONS['move_enemy'](move_node.available_actions['move'],
                                                                                self.action_handler)

    def hit(self, shooter):
        # if hit. get shocked.
        self.shock_timer = 4
        self.set_iso_texture(self.textures[1])


def create_bot(x, y, grid_2d) -> SimpleMoveBot:
    """
    Creates a simple bot that has a small logic that chooses where to move.
    :param x: the starting x pos in euclidean plane
    :param y: the starting y pos in euclidean plane
    :param grid_2d: the 2d grid of tiles to use
    :return: A simple move bot.
    """

    bot_text = isometric.generate_iso_data_other('bot')

    return SimpleMoveBot(x, y, bot_text, grid_2d)