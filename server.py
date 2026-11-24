import json
import sqlite3
from contextlib import closing
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlsplit

carpeta = Path(__file__).resolve().parent
base_datos = carpeta / "sugerencias.sqlite3"

campos = {
    "carrera": 80,
    "especializacion": 100,
    "idioma": 60,
    "motivo": 300
}

recomendaciones = [
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
]

archivos = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/front.css": ("front.css", "text/css; charset=utf-8"),
    "/script.js": ("script.js", "text/javascript; charset=utf-8"),
    "/imagen.jpg": ("imagen.jpg", "image/jpeg")
}


def preparar_base():
    with closing(sqlite3.connect(base_datos)) as conexion:
        with conexion:
            conexion.execute("""
                CREATE TABLE IF NOT EXISTS sugerencias (
                    id INTEGER PRIMARY KEY,
                    carrera TEXT NOT NULL,
                    especializacion TEXT NOT NULL,
                    idioma TEXT NOT NULL,
                    motivo TEXT NOT NULL
                )
            """)


def consultar_sugerencias():
    with closing(sqlite3.connect(base_datos)) as conexion:
        conexion.row_factory = sqlite3.Row
        filas = conexion.execute("""
            SELECT carrera, especializacion, idioma, motivo
            FROM sugerencias
            ORDER BY id DESC
        """).fetchall()

    return [dict(fila) for fila in filas]


class PaginaIdiomas(BaseHTTPRequestHandler):
    def enviar(self, codigo, contenido, tipo, sin_cache=False):
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(contenido)))
        self.send_header("X-Content-Type-Options", "nosniff")

        if sin_cache:
            self.send_header("Cache-Control", "no-store")

        self.end_headers()
        self.wfile.write(contenido)

    def enviar_json(self, codigo, datos):
        contenido = json.dumps(datos).encode("utf-8")
        self.enviar(codigo, contenido, "application/json; charset=utf-8",
                    sin_cache=True)

    def do_GET(self):
        ruta = urlsplit(self.path).path

        if ruta == "/api/idiomas":
            try:
                sugerencias = consultar_sugerencias()
            except sqlite3.Error:
                self.enviar_json(500, {"error": "No se pudieron consultar las sugerencias."})
                return

            self.enviar_json(200, {
                "carreras": recomendaciones,
                "parecidos": ["Portugués", "Italiano", "Francés"],
                "sugerencias": sugerencias
            })
            return

        if ruta not in archivos:
            self.send_error(404, "Ruta no encontrada")
            return

        nombre, tipo = archivos[ruta]

        try:
            contenido = (carpeta / nombre).read_bytes()
        except FileNotFoundError:
            self.send_error(404, "Archivo no encontrado")
            return

        self.enviar(200, contenido, tipo)

    def do_POST(self):
        if urlsplit(self.path).path != "/api/idiomas":
            self.enviar_json(404, {"error": "Ruta no encontrada."})
            return

        if self.headers.get_content_type() != "application/json":
            self.enviar_json(415, {"error": "El formulario debe enviarse como JSON."})
            return

        try:
            longitud = int(self.headers.get("Content-Length", "0"))

            if not 0 < longitud <= 8192:
                self.enviar_json(400, {"error": "Tamaño de formulario inválido."})
                return

            datos = json.loads(self.rfile.read(longitud).decode("utf-8"))
        except (ValueError, RecursionError):
            self.enviar_json(400, {"error": "El formulario no se pudo leer."})
            return

        if not isinstance(datos, dict):
            self.enviar_json(400, {"error": "El formulario no es válido."})
            return

        sugerencia = {}

        for campo, limite in campos.items():
            valor = datos.get(campo)

            if not isinstance(valor, str) or not valor.strip() or len(valor.strip()) > limite:
                self.enviar_json(400, {
                    "error": f"Completa el campo {campo}. Máximo: {limite} caracteres."
                })
                return

            sugerencia[campo] = valor.strip()

        try:
            with closing(sqlite3.connect(base_datos)) as conexion:
                with conexion:
                    conexion.execute("""
                        INSERT INTO sugerencias
                            (carrera, especializacion, idioma, motivo)
                        VALUES
                            (:carrera, :especializacion, :idioma, :motivo)
                    """, sugerencia)
        except (sqlite3.Error, UnicodeError):
            self.enviar_json(500, {"error": "No se pudo guardar la sugerencia."})
            return

        self.enviar_json(201, sugerencia)


if __name__ == "__main__":
    preparar_base()

    with HTTPServer(("127.0.0.1", 3000), PaginaIdiomas) as servidor:
        #print("Abre http://127.0.0.1:3000 en tu navegador", flush=True)
        print("https://edy-hoi.github.io/Desarrolloweb_hou/ en tu navegador", flush=True)

        try:
            servidor.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor detenido.")
