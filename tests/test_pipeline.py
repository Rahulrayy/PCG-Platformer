import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, MagicMock
import pytest

from level.generator import generate_raw_chunk
from validation.pipeline import validate

def _mock_chunk():
    chunk = MagicMock()
    chunk.entry_row = 2
    chunk.exit_row  = 2
    chunk.width_tiles = 160
    return chunk



class TestPipelineOrdering:
    """validate() must run BFS -> A* -> headless """

    def test_bfs_fail_skips_astar_and_headless(self):
        chunk = _mock_chunk()
        with patch('validation.pipeline.bfs',          return_value=False) as mock_bfs, \
             patch('validation.pipeline._graph') as mock_graph, \
             patch('validation.pipeline.run_headless') as mock_hl:
            result = validate(chunk)
        assert result is False
        mock_bfs.assert_called_once_with(chunk)
        mock_graph.a_star.assert_not_called()
        mock_hl.assert_not_called()

    def test_astar_fail_skips_headless(self):
        chunk = _mock_chunk()
        with patch('validation.pipeline.bfs',          return_value=True), \
             patch('validation.pipeline._graph') as mock_graph, \
             patch('validation.pipeline.run_headless') as mock_hl:
            mock_graph.a_star.return_value = False
            result = validate(chunk)
        assert result is False
        mock_hl.assert_not_called()

    def test_headless_fail_returns_false(self):
        chunk = _mock_chunk()
        with patch('validation.pipeline.bfs',          return_value=True), \
             patch('validation.pipeline._graph') as mock_graph, \
             patch('validation.pipeline.run_headless', return_value=False):
            mock_graph.a_star.return_value = True
            result = validate(chunk)
        assert result is False

    def test_all_pass_returns_true(self):
        chunk = _mock_chunk()
        with patch('validation.pipeline.bfs',          return_value=True), \
             patch('validation.pipeline._graph') as mock_graph, \
             patch('validation.pipeline.run_headless', return_value=True):
            mock_graph.a_star.return_value = True
            result = validate(chunk)
        assert result is True

    def test_astar_receives_correct_positions(self):
        """A* must be called with (col=0, entry_row) -> (col=159, exit_row)."""
        chunk = _mock_chunk()
        chunk.entry_row   = 3
        chunk.exit_row    = 5
        chunk.width_tiles = 160
        with patch('validation.pipeline.bfs',          return_value=True), \
             patch('validation.pipeline._graph') as mock_graph, \
             patch('validation.pipeline.run_headless', return_value=True):
            mock_graph.a_star.return_value = True
            validate(chunk)
        mock_graph.a_star.assert_called_once_with(
            (0, 3), (159, 5), chunk.tiles
        )



class TestPipelineIntegration:
    """Generate real chunks until one passes; verify the pipeline accepts it."""

    def test_valid_chunk_found_within_retries(self):
        MAX_ATTEMPTS = 300
        for _ in range(MAX_ATTEMPTS):
            chunk = generate_raw_chunk(index=0)
            if validate(chunk):
                return   # found one — test passes
        pytest.fail(f"No valid chunk found in {MAX_ATTEMPTS} attempts")

    def test_validate_is_deterministic(self):
        """The same chunk should always return the same result."""
        MAX_ATTEMPTS = 300
        valid_chunk = None
        for _ in range(MAX_ATTEMPTS):
            chunk = generate_raw_chunk(index=0)
            if validate(chunk):
                valid_chunk = chunk
                break
        assert valid_chunk is not None, "Could not find a valid chunk to test"
        # Run validate twice more on the same chunk object
        assert validate(valid_chunk) is True
        assert validate(valid_chunk) is True
