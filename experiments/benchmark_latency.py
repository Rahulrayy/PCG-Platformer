"""
measures whether the generation + validation pipeline is fast enough to keep up with the player.
Runs the full pipeline N times records time per chunk, and compares against the estimated time the player takes to cross a chunk at MOVE_SPEED.\
if too slow have to do multiple genaration/validation pipelines parallely
"""