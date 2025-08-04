import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from modules.chunk_engine import ChunkLayer
from modules.config import ApplicationConfig
from modules.schema import HexMapEngineConfig, HexMapCustomConfig, BackgroundConfig, HexMapShaderConfig, HexMapViewConfig

# Fixture for a mock ApplicationConfig
@pytest.fixture
def mock_app_config():
    """Provides a mock ApplicationConfig for testing ChunkEngine."""
    mock_config = MagicMock(spec=ApplicationConfig)
    mock_config.hex_map_engine = MagicMock(spec=HexMapEngineConfig)
    mock_config.hex_map_engine.chunk_size = 16
    mock_config.hex_map_engine.data_dimensions = 4
    mock_config.hex_map_custom = MagicMock(spec=HexMapCustomConfig)
    mock_config.hex_map_custom.default_cell_color = np.array([0.5, 0.5, 0.5, 1.0], dtype=np.float32)
    # Add other necessary config attributes if they are accessed by ChunkEngine
    mock_config.background = MagicMock(spec=BackgroundConfig)
    mock_config.hex_map_shaders = MagicMock(spec=HexMapShaderConfig)
    mock_config.hex_map_view = MagicMock(spec=HexMapViewConfig)
    return mock_config

# Mock global_coord_to_chunk_coord for predictable chunk/local coordinates
@pytest.fixture
def mock_global_coord_to_chunk_coord():
    """Mocks the global_coord_to_chunk_coord function."""
    with patch("modules.chunk_engine.global_coord_to_chunk_coord") as mock_func:
        # Default behavior: map global (x,y) to chunk (0,0) and local (x,y)
        mock_func.side_effect = lambda global_coords, chunk_size: (
            global_coords[0] // chunk_size,
            global_coords[1] // chunk_size,
            global_coords[0] % chunk_size,
            global_coords[1] % chunk_size
        )
        yield mock_func

# Test cases for ChunkEngine
def test_chunk_engine_initialization(mock_app_config):
    """Test that ChunkEngine initializes correctly."""
    engine = ChunkLayer(mock_app_config)
    assert isinstance(engine.chunks, dict)
    assert len(engine.chunks) == 0
    assert isinstance(engine.dirty_chunks, set)
    assert len(engine.dirty_chunks) == 0
    assert isinstance(engine.modified_cells, set)
    assert len(engine.modified_cells) == 0

def test_get_or_create_chunk_new(mock_app_config):
    """Test creating a new chunk."""
    engine = ChunkLayer(mock_app_config)
    chunk_coord = (0, 0)
    chunk_data = engine._get_or_create_chunk(chunk_coord)

    assert chunk_coord in engine.chunks
    assert isinstance(chunk_data, np.ndarray)
    assert chunk_data.shape == (mock_app_config.hex_map_engine.chunk_size,
                                mock_app_config.hex_map_engine.chunk_size,
                                mock_app_config.hex_map_engine.data_dimensions)
    # Check if initialized with default color
    assert np.all(chunk_data == mock_app_config.hex_map_custom.default_cell_color)

def test_get_or_create_chunk_existing(mock_app_config):
    """Test retrieving an existing chunk."""
    engine = ChunkLayer(mock_app_config)
    chunk_coord = (0, 0)
    # Create it first
    engine._get_or_create_chunk(chunk_coord)
    # Modify some data to ensure it's the same chunk
    engine.chunks[chunk_coord][0, 0] = np.array([1.0, 0.0, 0.0, 1.0], dtype=np.float32)

    retrieved_chunk_data = engine._get_or_create_chunk(chunk_coord)
    assert np.all(retrieved_chunk_data[0, 0] == np.array([1.0, 0.0, 0.0, 1.0], dtype=np.float32))
    assert retrieved_chunk_data is engine.chunks[chunk_coord] # Ensure it's the same object

@pytest.mark.parametrize("global_coords, expected_chunk_coord, expected_local_coord", [
    ((0, 0), (0, 0), (0, 0)),
    ((15, 15), (0, 0), (15, 15)),
    ((16, 0), (1, 0), (0, 0)),
    ((31, 17), (1, 1), (15, 1)),
])
def test_set_cell_data(mock_app_config, mock_global_coord_to_chunk_coord,
                       global_coords, expected_chunk_coord, expected_local_coord):
    """Test setting cell data and marking chunk as dirty."""
    engine = ChunkLayer(mock_app_config)
    test_data = np.array([1.0, 0.0, 0.0, 1.0], dtype=np.float32) # Red color

    engine.set_cell_data(global_coords, test_data)

    # Verify chunk is created/updated and data is set
    chunk_data = engine.chunks.get(expected_chunk_coord)
    assert chunk_data is not None
    assert np.all(chunk_data[expected_local_coord[0], expected_local_coord[1]] == test_data)

    # Verify chunk is marked dirty
    assert expected_chunk_coord in engine.dirty_chunks
    # Verify cell is added to modified_cells
    assert global_coords in engine.modified_cells

def test_get_cell_data(mock_app_config, mock_global_coord_to_chunk_coord):
    """Test retrieving cell data."""
    engine = ChunkLayer(mock_app_config)
    global_coords = (5, 5)
    test_data = np.array([0.0, 1.0, 0.0, 1.0], dtype=np.float32) # Green color

    # Set data first
    engine.set_cell_data(global_coords, test_data)

    # Retrieve data
    retrieved_data = engine.get_cell_data(global_coords)
    assert np.all(retrieved_data == test_data)

    # Test getting data from a non-existent cell (should return default color)
    non_existent_coords = (100, 100)
    default_data = engine.get_cell_data(non_existent_coords)
    assert np.all(default_data == mock_app_config.hex_map_custom.default_cell_color)

def test_delete_cell_data(mock_app_config, mock_global_coord_to_chunk_coord):
    """Test deleting cell data."""
    engine = ChunkLayer(mock_app_config)
    global_coords = (7, 7)
    test_data = np.array([0.0, 0.0, 1.0, 1.0], dtype=np.float32) # Blue color

    # Set data first
    engine.set_cell_data(global_coords, test_data)
    assert global_coords in engine.modified_cells
    chunk_coord = (global_coords[0] // mock_app_config.hex_map_engine.chunk_size,
                   global_coords[1] // mock_app_config.hex_map_engine.chunk_size)
    assert chunk_coord in engine.dirty_chunks # Should be dirty from set_cell_data

    # Clear dirty chunks for this test's purpose
    engine.dirty_chunks.clear()
    assert chunk_coord not in engine.dirty_chunks

    # Delete data
    engine.delete_cell_data(global_coords)

    # Verify data is reset to default
    retrieved_data = engine.get_cell_data(global_coords)
    assert np.all(retrieved_data == mock_app_config.hex_map_custom.default_cell_color)

    # Verify chunk is marked dirty again
    assert chunk_coord in engine.dirty_chunks
    # Verify cell is removed from modified_cells
    assert global_coords not in engine.modified_cells

    # Test deleting a non-modified cell (should do nothing)
    non_modified_coords = (8, 8)
    engine.delete_cell_data(non_modified_coords)
    # No change to dirty_chunks or modified_cells expected
    assert chunk_coord in engine.dirty_chunks # Still dirty from previous operation
    assert non_modified_coords not in engine.modified_cells

def test_get_chunk_data(mock_app_config):
    """Test retrieving chunk data."""
    engine = ChunkLayer(mock_app_config)
    chunk_coord = (0, 0)
    chunk_data = engine.get_chunk_data(chunk_coord)

    assert isinstance(chunk_data, np.ndarray)
    assert chunk_data.shape == (mock_app_config.hex_map_engine.chunk_size,
                                mock_app_config.hex_map_engine.chunk_size,
                                mock_app_config.hex_map_engine.data_dimensions)
    assert np.all(chunk_data == mock_app_config.hex_map_custom.default_cell_color)
    assert chunk_data is engine.chunks[chunk_coord] # Ensure it's the same object

def test_get_and_clear_dirty_chunks(mock_app_config, mock_global_coord_to_chunk_coord):
    """Test getting and clearing dirty chunks."""
    engine = ChunkLayer(mock_app_config)
    engine.set_cell_data((0, 0), np.array([1,0,0,1], dtype=np.float32))
    engine.set_cell_data((17, 17), np.array([0,1,0,1], dtype=np.float32)) # In chunk (1,1)

    dirty_chunks = engine.get_and_clear_dirty_chunks()
    assert len(dirty_chunks) == 2
    assert (0, 0) in dirty_chunks
    assert (1, 1) in dirty_chunks
    assert len(engine.dirty_chunks) == 0 # Should be cleared

    # Call again, should be empty
    dirty_chunks_again = engine.get_and_clear_dirty_chunks()
    assert len(dirty_chunks_again) == 0

def test_reset(mock_app_config, mock_global_coord_to_chunk_coord):
    """Test resetting the chunk engine."""
    engine = ChunkLayer(mock_app_config)
    engine.set_cell_data((0, 0), np.array([1,0,0,1], dtype=np.float32))
    engine.set_cell_data((17, 17), np.array([0,1,0,1], dtype=np.float32))

    assert len(engine.chunks) > 0
    assert len(engine.dirty_chunks) > 0
    assert len(engine.modified_cells) > 0

    engine.reset()

    assert len(engine.chunks) == 0
    assert len(engine.dirty_chunks) == 0
    assert len(engine.modified_cells) == 0
    # Verify that calling get_cell_data on a previously modified cell
    # now returns the default color (as the chunk would be recreated)
    assert np.all(engine.get_cell_data((0,0)) == mock_app_config.hex_map_custom.default_cell_color)
