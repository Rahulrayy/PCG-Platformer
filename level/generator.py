"""

calls cellular_automata.py to get a raw tile array..... wraps it in a Chunk then passes it through the validation pipeline
,and if it fails generates a new one and tries again.

 Run in a background thread so the player never waits.should maintains a queue of pre-validated chunks ready to hand to chunk_manager.py.

"""