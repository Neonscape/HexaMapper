from utils.helpers import load_program
from loguru import logger
from OpenGL.GL import *

class ShaderManager:
    """
    Manages OpenGL shader programs, Vertex Buffer Objects (VBOs),
    and Vertex Array Objects (VAOs) for the application.
    """
    def __init__(self):
        """
        Initializes the ShaderManager with empty dictionaries for programs, VBOs, and VAOs.
        """
        self.registered_programs: dict[str, tuple[str, str]] = {}
        self.compiled_programs : dict[str, int] = {}
        self.uniforms: dict[str, list[str]] = {}
        self.uniform_locations: dict[str, dict[str, int]] = {}
        self.vbos: dict[str, int] = {}
        self.vaos: dict[str, int] = {}
    
    def compile_all_programs(self):
        """
        Compiles all registered shader programs. Logs success or error for each program.
        """
        logger.info("Starting shader compilation...")
        error_flag = False
        for name, (vertex_shader_path, fragment_shader_path) in self.registered_programs.items():
            program = load_program(vertex_shader_path, fragment_shader_path)
            if program is None:
                error_flag = True
            self.compiled_programs[name] = program
            
            self.uniform_locations[name] = dict()
            for uniform in self.uniforms[name]:
                self.uniform_locations[name][uniform] = glGetUniformLocation(program, uniform)
            logger.info(f"Compiled program {name} successfully.")
        
        logger.info(f"Shader compilation finished " + ("with errors." if error_flag else "successfully."))
    
    def register_program(self, name: str, vertex_shader_path: str, fragment_shader_path: str, uniforms: list[str] = None):
        """
        Registers a shader program by name and its vertex/fragment shader file paths.

        :param name: The unique name for the shader program.
        :type name: str
        :param vertex_shader_path: The file path to the vertex shader.
        :type vertex_shader_path: str
        :param fragment_shader_path: The file path to the fragment shader.
        :type fragment_shader_path: str
        """
        self.registered_programs[name] = (vertex_shader_path, fragment_shader_path)
        if uniforms is not None:
            self.uniforms[name] = uniforms

    def get_program(self, name: str) -> int:
        """
        Retrieves a compiled OpenGL shader program by its registered name.

        :param name: The name of the program.
        :type name: str
        :return: The OpenGL program ID.
        :rtype: int
        """
        return self.compiled_programs[name]
    
    def get_uniforms(self, name: str) -> dict[str, int]:
        return self.uniform_locations[name]

    def remove_program(self, name: str):
        """
        Removes a compiled shader program from the manager.

        :param name: The name of the program to remove.
        :type name: str
        """
        del self.compiled_programs[name]

    def clear_programs(self):
        """
        Clears all registered and compiled shader programs.
        """
        self.compiled_programs.clear()
        self.registered_programs.clear()
        
    def add_vbo(self, name: str) -> int:
        """
        Generates a new OpenGL Vertex Buffer Object (VBO) and registers it by name.

        :param name: The unique name for the VBO.
        :type name: str
        :return: The OpenGL VBO ID.
        :rtype: int
        """
        vbo_id = glGenBuffers(1)
        self.vbos[name] = vbo_id
        return vbo_id

    def get_vbo(self, name: str) -> int:
        """
        Retrieves an OpenGL VBO by its registered name.

        :param name: The name of the VBO.
        :type name: str
        :return: The OpenGL VBO ID.
        :rtype: int
        """
        return self.vbos[name]

    def remove_vbo(self, name: str):
        """
        Deletes an OpenGL VBO and removes it from the manager.

        :param name: The name of the VBO to remove.
        :type name: str
        """
        glDeleteBuffers(1, [self.vbos[name]])
        del self.vbos[name]

    def clear_vbos(self):
        """
        Deletes all managed VBOs and clears the VBO dictionary.
        """
        for vbo_id in self.vbos.values():
            glDeleteBuffers(1, [vbo_id])
        self.vbos.clear()
        
    def add_vao(self, name: str) -> int:
        """
        Generates a new OpenGL Vertex Array Object (VAO) and registers it by name.

        :param name: The unique name for the VAO.
        :type name: str
        :return: The OpenGL VAO ID.
        :rtype: int
        """
        vao_id = glGenVertexArrays(1)
        self.vaos[name] = vao_id
        return vao_id

    def get_vao(self, name: str) -> int:
        """
        Retrieves an OpenGL VAO by its registered name.

        :param name: The name of the VAO.
        :type name: str
        :return: The OpenGL VAO ID.
        :rtype: int
        """
        return self.vaos[name]

    def remove_vao(self, name: str):
        """
        Deletes an OpenGL VAO and removes it from the manager.

        :param name: The name of the VAO to remove.
        :type name: str
        """
        glDeleteVertexArrays(1, [self.vaos[name]])
        del self.vaos[name]

    def clear_vaos(self):
        """
        Deletes all managed VAOs and clears the VAO dictionary.
        """
        for vao_id in self.vaos.values():
            glDeleteVertexArrays(1, [vao_id])
        self.vaos.clear()
