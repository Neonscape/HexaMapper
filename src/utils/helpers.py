from OpenGL.GL import *
from OpenGL.GL.shaders import compileShader, compileProgram
import os
from loguru import logger

def load_file(filepath: str) -> str:
    """
    Loads a file from the given filepath and returns its content as a string.

    :param filepath: The path to the file.
    :type filepath: str
    :return: The content of the file, or None if the file is not found.
    :rtype: str | None
    """
    try:
        with open(filepath, 'r') as file:
            return file.read()
    except FileNotFoundError:
        logger.error(f"File {filepath} not found, returning None")
        return None

def load_program(vertex_file_path: str, fragment_file_path: str) -> int | None:
    """
    Loads, compiles, and links vertex and fragment shaders into an OpenGL program.

    :param vertex_file_path: The path to the vertex shader file.
    :type vertex_file_path: str
    :param fragment_file_path: The path to the fragment shader file.
    :type fragment_file_path: str
    :return: The OpenGL program ID if compilation and linking are successful, otherwise None.
    :rtype: int | None
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
