const formulario = document.getElementById("formulario-sugerencia");
const boton = formulario.querySelector("button");
const estado = document.getElementById("estado");
const listaGuardadas = document.getElementById("lista-guardadas");
const sinSugerencias = document.getElementById("sin-sugerencias");

function crearSugerencia(dato) {
    const elemento = document.createElement("li");
    const titulo = document.createElement("strong");

    if (dato.especializacion) {
        titulo.textContent = dato.carrera + " (" + dato.especializacion + "): ";
    } else {
        titulo.textContent = dato.carrera + ": ";
    }

    elemento.append(titulo, dato.idioma + ". " + dato.motivo);
    return elemento;
}

async function cargarSugerencias() {
    boton.disabled = true;

    try {
        const respuesta = await fetch("/api/idiomas");

        if (!respuesta.ok) {
            throw new Error("No se pudieron consultar las sugerencias.");
        }

        const datos = await respuesta.json();

        listaGuardadas.replaceChildren(...datos.sugerencias.map(crearSugerencia));
        sinSugerencias.hidden = datos.sugerencias.length > 0;

        const listaCarreras = document.getElementById("lista-carreras");
        const idiomasParecidos = document.getElementById("idiomas-parecidos");

        if (listaCarreras) {
            listaCarreras.replaceChildren(...datos.carreras.map(crearSugerencia));
        }

        if (idiomasParecidos) {
            idiomasParecidos.textContent = datos.parecidos.join(", ") +
                " comparten raíces latinas con el español.";
        }

        boton.disabled = false;
    } catch {
        estado.textContent = "No se pudo conectar con Python. Abre la página desde el servidor local.";
    }
}

formulario.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    boton.disabled = true;
    estado.textContent = "Guardando sugerencia…";

    const datos = Object.fromEntries(new FormData(formulario));

    try {
        const respuesta = await fetch("/api/idiomas", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(datos)
        });

        const sugerencia = await respuesta.json();

        if (!respuesta.ok) {
            estado.textContent = sugerencia.error;
            return;
        }

        listaGuardadas.prepend(crearSugerencia(sugerencia));
        sinSugerencias.hidden = true;
        formulario.reset();
        estado.textContent = "Sugerencia guardada.";
    } catch {
        estado.textContent = "No se pudo confirmar el guardado. Actualiza la página para comprobarlo.";
    } finally {
        boton.disabled = false;
    }
});

cargarSugerencias();
