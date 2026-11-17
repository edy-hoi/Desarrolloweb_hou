import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlsplit
"/script.js": ("script.js", "text/javascript; charset=utf-8"),

carpeta = Path(__file__).resolve().parent

# Sugerencias que se muestran en la página
datos = {
    "carreras": [
        {
            "carrera": "Tecnología",
            "idioma": "Inglés",
            "motivo": "Para consultar documentación y recursos de programación."
        },
        {
            "carrera": "Negocios",
            "idioma": "Portugués",
            "motivo": "Si te interesa trabajar con clientes o empresas de Brasil."
        },
        {
            "carrera": "Turismo",
            "idioma": "Inglés",
            "motivo": "Para comunicarte con visitantes que hablan inglés."
        }
    ],
    "parecidos": ["Portugués", "Italiano", "Francés"]
}

# Archivos que puede pedir el navegador
archivos = {
    "/": ("front.html", "text/html; charset=utf-8"),
    "/front.html": ("front.html", "text/html; charset=utf-8"),
    "/front.css": ("front.css", "text/css; charset=utf-8"),
    "/imagen.jpg": ("imagen.jpg", "image/jpeg")
}


class PaginaIdiomas(BaseHTTPRequestHandler):
    def do_GET(self):
        ruta = urlsplit(self.path).path

        if ruta == "/api/idiomas":
            contenido = json.dumps(datos, ensure_ascii=False).encode("utf-8")
            tipo = "application/json; charset=utf-8"
        elif ruta in archivos:
            nombre, tipo = archivos[ruta]
            try:
                contenido = (carpeta / nombre).read_bytes()
            except FileNotFoundError:
                self.send_error(404, "Archivo no encontrado")
                return
        else:
            self.send_error(404, "Ruta no encontrada")
            return

        self.send_response(200)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(contenido)))
        self.end_headers()
        self.wfile.write(contenido)


if __name__ == "__main__":
    with HTTPServer(("127.0.0.1", 3000), PaginaIdiomas) as servidor:
        print("Abre http://127.0.0.1:3000 en tu navegador", flush=True)
        try:
            servidor.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor detenido.")
