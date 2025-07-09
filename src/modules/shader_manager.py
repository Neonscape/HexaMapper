from utils.helpers import load_program

class ShaderManager:
    def __init__(self):
        self.programs : dict[str, int] = {}
        self.vbos: dict[str, int] = {}
        self.vaos: dict[str, int] = {}
    
    def add_program(self, name: str, vertex_shader_path: str, fragment_shader_path: str):
        program = load_program(vertex_shader_path, fragment_shader_path)
        self.programs[name] = program

    def get_program(self, name: str):
        return self.programs[name]

    def remove_program(self, name: str):
        del self.programs[name]

    def clear_programs(self):
        self.programs.clear()
        
    def add_vbo(self, name: str, vbo_id: int):
        self.vbos[name] = vbo_id

    def get_vbo(self, name: str) -> int:
        return self.vbos[name]

    def remove_vbo(self, name: str):
        del self.vbos[name]

    def clear_vbos(self):
        self.vbos.clear()
        
    def add_vao(self, name: str, vao_id: int):
        self.vaos[name] = vao_id

    def get_vao(self, name: str) -> int:
        return self.vaos[name]

    def remove_vao(self, name: str):
        del self.vaos[name]

    def clear_vaos(self):
        self.vaos.clear()
