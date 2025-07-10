from utils.helpers import load_program
from loguru import logger
from OpenGL.GL import *

class ShaderManager:
    def __init__(self):
        self.registered_programs: dict[str, tuple[str, str]] = {}
        self.compiled_programs : dict[str, int] = {}
        self.vbos: dict[str, int] = {}
        self.vaos: dict[str, int] = {}
    
    def compile_all_programs(self):
        logger.info("Starting shader compilation...")
        error_flag = False
        for name, (vertex_shader_path, fragment_shader_path) in self.registered_programs.items():
            program = load_program(vertex_shader_path, fragment_shader_path)
            if program is None:
                error_flag = True
            self.compiled_programs[name] = program
            logger.info(f"Compiled program {name} successfully.")
        
        logger.info(f"Shader compilation finished " + ("with errors." if error_flag else "successfully."))
    
    def register_program(self, name: str, vertex_shader_path: str, fragment_shader_path: str):
        self.registered_programs[name] = (vertex_shader_path, fragment_shader_path)

    def get_program(self, name: str):
        return self.compiled_programs[name]

    def remove_program(self, name: str):
        del self.compiled_programs[name]

    def clear_programs(self):
        self.compiled_programs.clear()
        self.registered_programs.clear()
        
    def add_vbo(self, name: str):
        vbo_id = glGenBuffers(1)
        self.vbos[name] = vbo_id
        return vbo_id

    def get_vbo(self, name: str) -> int:
        return self.vbos[name]

    def remove_vbo(self, name: str):
        glDeleteBuffers(1, [self.vbos[name]])
        del self.vbos[name]

    def clear_vbos(self):
        for vbo_id in self.vbos.values():
            glDeleteBuffers(1, [vbo_id])
        self.vbos.clear()
        
    def add_vao(self, name: str):
        vao_id = glGenVertexArrays(1)
        self.vaos[name] = vao_id
        return vao_id

    def get_vao(self, name: str) -> int:
        return self.vaos[name]

    def remove_vao(self, name: str):
        glDeleteVertexArrays(1, [self.vaos[name]])
        del self.vaos[name]

    def clear_vaos(self):
        for vao_id in self.vaos.values():
            glDeleteVertexArrays(1, [vao_id])
        self.vaos.clear()

shader_manager = ShaderManager()