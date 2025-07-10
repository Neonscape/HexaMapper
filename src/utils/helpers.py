from OpenGL.GL import *
from OpenGL.GL.shaders import compileShader, compileProgram
import os
from loguru import logger

def load_file(filepath: str) -> str:
    """Load a file and return its content.

    Args:
        filepath (str): _description_

    Returns:
        str: _description_
    """
    try:
        file = open(filepath, 'r')
        return file.read()
    except FileNotFoundError:
        logger.error(f"File {filepath} not found, returning None");
        return None

def load_program(vertex_file_path: str, fragment_file_path: str) -> int | None:
    """Load and compile shaders and use them in a program.

    Args:
        vertex_file_path (str): _description_
        fragment_file_path (str): _description_

    Returns:
        int: _description_
    """
    
    v_file, f_file = load_file(vertex_file_path), load_file(fragment_file_path)

    if v_file is None or f_file is None:
        logger.error("Error loading shaders, returning None")
        return None

    try:
        vertex_shader = compileShader(v_file, GL_VERTEX_SHADER)
        
    except Exception as e:
        logger.error(f"Error compiling shader {vertex_file_path}: {e}")
        return None
    
    try:
        fragment_shader = compileShader(f_file, GL_FRAGMENT_SHADER)
    except Exception as e:
        logger.error(f"Error compiling shader {fragment_file_path}: {e}")
        return None

    try:
        program = compileProgram(vertex_shader, fragment_shader)
    except Exception as e:
        logger.error(f"Error compiling program: {e}")
        return None

    return program