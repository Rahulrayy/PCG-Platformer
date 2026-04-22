"""
Wraps headless_runner.py as a Gymnasium Env.

defines the obv space (local tile window around the player), action space (left, right, jump), reward signal (positive for rightward progress, negative on death), and reset methods.
copy same calues from config
also make sure some delay is there between simulated movements so that a human is mimiced

"""