import tornado.ioloop
import tornado.web
import json

# Simulando banco de dados de módulos
modules_data = [
    {
        "id": 1,
        "title": "Módulo 1",
        "description": "Aprenda conteúdos essenciais do Módulo 1.",
        "lessons": [
            {"id": "1-1", "title": "Aula 1-1", "video": "https://www.youtube.com/embed/dQw4w9WgXcQ", "task": "Atividade 1-1"},
            {"id": "1-2", "title": "Aula 1-2", "video": "https://www.youtube.com/embed/dQw4w9WgXcQ", "task": "Atividade 1-2"}
        ],
        "image": "https://via.placeholder.com/140x90.png?text=Módulo+1"
    },
    {
        "id": 2,
        "title": "Módulo 2",
        "description": "Aprenda conteúdos essenciais do Módulo 2.",
        "lessons": [
            {"id": "2-1", "title": "Aula 2-1", "video": "https://www.youtube.com/embed/dQw4w9WgXcQ", "task": "Atividade 2-1"}
        ],
        "image": "https://via.placeholder.com/140x90.png?text=Módulo+2"
    }
]

class ModulesHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(modules_data))

