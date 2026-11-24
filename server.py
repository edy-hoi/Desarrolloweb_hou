import json
import os
import re
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

carpeta = Path(__file__).resolve().parent
supabase_url = os.environ.get("SUPABASE_URL", "").strip().rstrip("/")
supabase_key = os.environ.get("SUPABASE_SECRET_KEY", "").strip()

campos = {
    "carrera": 80,
    "especializacion": 100,
    "idioma": 60,
    "motivo": 300
}

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
            "motivo": "Para trabajar con clientes o empresas de Brasil."
        },
        {
            "carrera": "Turismo",
            "idioma": "Inglés",
            "motivo": "Para comunicarte con visitantes que hablan inglés."
        }
    ],
    "parecidos": ["Portugués", "Italiano", "Francés"]
}

archivos = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/front.css": ("front.css", "text/css; charset=utf-8"),
    "/script.js": ("script.js", "text/javascript; charset=utf-8"),
    "/imagen.jpg": ("imagen.jpg", "image/jpeg"),
    "/assets/globo-terraqueo-multilingue.png": (
        "assets/globo-terraqueo-multilingue.png", "image/png"
    )
}


# Envía una petición a la tabla sugerencias de Supabase
def consultar_supabase(metodo, filtros, datos_envio=None):
    url = f"{supabase_url}/rest/v1/sugerencias?{urlencode(filtros)}"
    cabeceras = {"apikey": supabase_key, "Accept": "application/json"}
    contenido = None

    if metodo != "GET":
        cabeceras["Prefer"] = "return=representation"

    if datos_envio is not None:
        cabeceras["Content-Type"] = "application/json"
        contenido = json.dumps(datos_envio).encode("utf-8")

    peticion = Request(url, data=contenido, headers=cabeceras, method=metodo)

    with urlopen(peticion, timeout=10) as respuesta:
        filas = json.load(respuesta)
        for fila in filas:
            fila["id"] = str(fila["id"])
        return filas


class PaginaIdiomas(BaseHTTPRequestHandler):
    def enviar(self, codigo, contenido, tipo):
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(contenido)))
        self.send_header("X-Content-Type-Options", "nosniff")

        if tipo.startswith("application/json"):
            self.send_header("Cache-Control", "no-store")

        self.end_headers()
        self.wfile.write(contenido)

    def enviar_json(self, codigo, respuesta):
        contenido = json.dumps(respuesta, ensure_ascii=False).encode("utf-8")
        self.enviar(codigo, contenido, "application/json; charset=utf-8")

    def error_supabase(self, error):
        detalle = error.code if isinstance(error, HTTPError) else type(error).__name__
        self.log_error("Supabase: %s", detalle)
        self.enviar_json(502, {
            "error": "Supabase no pudo completar la operación. Revisa la terminal."
        })

    # Consultar sugerencias o abrir un archivo de la página
    def do_GET(self):
        ruta = urlsplit(self.path).path

        if ruta == "/api/idiomas":
            try:
                sugerencias = consultar_supabase("GET", {
                    "select": "id,carrera,especializacion,idioma,motivo",
                    "order": "id.desc"
                })
            except (URLError, TimeoutError, ValueError) as error:
                self.error_supabase(error)
                return

            self.enviar_json(200, {**datos, "sugerencias": sugerencias})
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

    # Insertar una sugerencia
    def do_POST(self):
        if urlsplit(self.path).path != "/api/idiomas":
            self.enviar_json(404, {"error": "Ruta no encontrada."})
            return

        self.guardar_sugerencia("POST", {})

    # Actualizar o borrar una sugerencia por su ID
    def do_PATCH(self):
        self.cambiar_sugerencia("PATCH")

    def do_DELETE(self):
        self.cambiar_sugerencia("DELETE")

    def cambiar_sugerencia(self, metodo):
        ruta = urlsplit(self.path).path
        coincidencia = re.fullmatch(r"/api/idiomas/([1-9][0-9]{0,18})", ruta)

        if not coincidencia or int(coincidencia[1]) > 9223372036854775807:
            self.enviar_json(404, {"error": "Ruta no encontrada."})
            return

        filtro = {"id": "eq." + coincidencia[1]}

        if metodo == "PATCH":
            self.guardar_sugerencia(metodo, filtro)
        else:
            self.enviar_cambio(metodo, filtro)

    def guardar_sugerencia(self, metodo, filtro):
        if self.headers.get_content_type() != "application/json":
            self.enviar_json(415, {"error": "El formulario debe enviarse como JSON."})
            return

        try:
            longitud = int(self.headers.get("Content-Length", "0"))

            if not 0 < longitud <= 8192:
                self.enviar_json(400, {"error": "Tamaño de formulario inválido."})
                return

            formulario = json.loads(self.rfile.read(longitud).decode("utf-8"))
        except (ValueError, RecursionError):
            self.enviar_json(400, {"error": "El formulario no se pudo leer."})
            return

        if not isinstance(formulario, dict):
            self.enviar_json(400, {"error": "El formulario no es válido."})
            return

        sugerencia = {}

        for campo, limite in campos.items():
            valor = formulario.get(campo)

            if not isinstance(valor, str) or not valor.strip() or len(valor.strip()) > limite:
                self.enviar_json(400, {
                    "error": f"Revisa el campo {campo}. Máximo: {limite} caracteres."
                })
                return

            sugerencia[campo] = valor.strip()

        self.enviar_cambio(metodo, filtro, sugerencia)

    def enviar_cambio(self, metodo, filtro, sugerencia=None):
        try:
            filas = consultar_supabase(metodo, filtro, sugerencia)
        except (URLError, TimeoutError, ValueError) as error:
            self.error_supabase(error)
            return

        if not filas:
            self.enviar_json(404, {"error": "La sugerencia ya no existe."})
            return

        codigo = 201 if metodo == "POST" else 200
        self.enviar_json(codigo, filas[0])


if __name__ == "__main__":
    if not re.fullmatch(r"https://[a-z0-9-]+\.supabase\.co", supabase_url):
        raise SystemExit("Configura SUPABASE_URL con la URL de tu proyecto.")

#<<<<<<< HEAD
#    with HTTPServer(("127.0.0.1", 3000), PaginaIdiomas) as servidor:
#        print("Abre http://127.0.0.1:3000 en tu navegador", flush=True)
#        #print("https://edy-hoi.github.io/Desarrolloweb_hou/ en tu navegador", flush=True)
#=======
#    if not supabase_key.startswith("sb_secret_"):
#        raise SystemExit("Configura SUPABASE_SECRET_KEY en Codespaces.")

#    with HTTPServer(("0.0.0.0", 3000), PaginaIdiomas) as servidor:
#        print("Abre la página desde el puerto 3000 de Codespaces.", flush=True)
#>>>>>>> 4ba7589 (Corrige servidor web y soporte HEAD)

    if not supabase_key.startswith("sb_secret_"):
        raise SystemExit("Configura SUPABASE_SECRET_KEY en Codespaces.")

    with HTTPServer(("0.0.0.0", 3000), PaginaIdiomas) as servidor:
        print("Abre la página desde el puerto 3000 de Codespaces.", flush=True)

#=======
        try:
            servidor.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor detenido.")