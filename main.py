import arcade
from level import cellular_automata
from game.window import GameWindow


def main():
    # TODO remove, just demo
    cellular_automata.get_raw_tile_array()
    window = GameWindow()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()