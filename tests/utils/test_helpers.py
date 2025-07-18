import pytest
from unittest.mock import patch, mock_open
from utils.helpers import load_file, load_program

# Test cases for load_file
def test_load_file_success():
    """Test that load_file successfully reads a file."""
    mock_file_content = "Hello, this is a test file."
    with patch("builtins.open", mock_open(read_data=mock_file_content)) as mock_file:
        # Patch utils.helpers.get_resource_path because load_file imports it directly
        with patch("utils.helpers.get_resource_path", return_value="/mock/path/test.txt") as mock_get_resource_path:
            content = load_file("test.txt")
            assert content == mock_file_content
            mock_get_resource_path.assert_called_once_with("test.txt")
            mock_file.assert_called_once_with("/mock/path/test.txt", 'r')

def test_load_file_not_found():
    """Test that load_file returns None when the file is not found."""
    with patch("builtins.open", side_effect=FileNotFoundError):
        with patch("utils.helpers.get_resource_path", return_value="/mock/path/nonexistent.txt"):
            content = load_file("nonexistent.txt")
            assert content is None

# Test cases for load_program (requires mocking OpenGL calls)
# This is a more complex test due to OpenGL dependencies.
# For simplicity, we'll mock the compileShader and compileProgram functions.
# In a real scenario, you might use a library like `PyOpenGL_accelerate`
# or a dedicated test framework for OpenGL if you need to test actual GL calls.

@patch("utils.helpers.compileShader")
@patch("utils.helpers.compileProgram")
@patch("utils.helpers.load_file")
def test_load_program_success(mock_load_file, mock_compileProgram, mock_compileShader):
    """Test that load_program successfully compiles and links shaders."""
    mock_load_file.side_effect = ["vertex_shader_code", "fragment_shader_code"]
    mock_compileShader.side_effect = [1, 2] # Mock shader IDs
    mock_compileProgram.return_value = 3 # Mock program ID

    program_id = load_program("vertex.glsl", "fragment.glsl")

    assert program_id == 3
    assert mock_load_file.call_count == 2
    # Use assert_any_call or assert_has_calls when multiple calls are expected
    mock_compileShader.assert_any_call("vertex_shader_code", 35633) # GL_VERTEX_SHADER
    mock_compileShader.assert_any_call("fragment_shader_code", 35632) # GL_FRAGMENT_SHADER
    mock_compileProgram.assert_called_once_with(1, 2)

@patch("utils.helpers.load_file", return_value=None) # Mock first call to fail
def test_load_program_load_file_failure(mock_load_file):
    """Test that load_program returns None if file loading fails."""
    program_id = load_program("vertex.glsl", "fragment.glsl")
    assert program_id is None
    # load_file is called only once now due to early exit
    assert mock_load_file.call_count == 1
    mock_load_file.assert_called_once_with("vertex.glsl")

@patch("utils.helpers.compileShader", side_effect=Exception("Shader compile error"))
@patch("utils.helpers.load_file", side_effect=["vertex_code", "fragment_code"])
def test_load_program_compile_shader_failure(mock_load_file, mock_compileShader):
    """Test that load_program returns None if shader compilation fails."""
    program_id = load_program("vertex.glsl", "fragment.glsl")
    assert program_id is None
    mock_compileShader.assert_called_once() # Should be called for vertex shader

@patch("utils.helpers.compileProgram", side_effect=Exception("Program link error"))
@patch("utils.helpers.compileShader", side_effect=[1, 2])
@patch("utils.helpers.load_file", side_effect=["vertex_code", "fragment_code"])
def test_load_program_link_failure(mock_load_file, mock_compileShader, mock_compileProgram):
    """Test that load_program returns None if program linking fails."""
    program_id = load_program("vertex.glsl", "fragment.glsl")
    assert program_id is None
    mock_compileProgram.assert_called_once()
