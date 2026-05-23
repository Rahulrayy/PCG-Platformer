import json
from pathlib import Path
from config import TILE_SIZE

_SAVE_FILE = Path(__file__).parent.parent / "highscore.json"


class Score:
    """
    Tracks distance for the current run and the all-time best across sessions.
    Call reset() at the start of each run, save() when the run ends.
    """

    def __init__(self):
        self._run_x: float = 0.0
        self.best_tiles: int = self._load()

    def update(self, player_x: float):
        if player_x > self._run_x:
            self._run_x = player_x

    def reset(self):
        self._run_x = 0.0

    def save(self):
        if self.tiles_traveled > self.best_tiles:
            self.best_tiles = self.tiles_traveled
            try:
                _SAVE_FILE.write_text(json.dumps({"best": self.best_tiles}))
            except OSError:
                pass

    @property
    def tiles_traveled(self) -> int:
        return int(self._run_x / TILE_SIZE)

    def _load(self) -> int:
        try:
            return json.loads(_SAVE_FILE.read_text()).get("best", 0)
        except (OSError, json.JSONDecodeError):
            return 0
