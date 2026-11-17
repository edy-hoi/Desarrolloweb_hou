 async function cargarIdiomas() {
   const lista = document.getElementById("lista-carreras");
   const parecidos = document.getElementById("idiomas-parecidos");
   try {
     const respuesta = await fetch("/api/idiomas");
     if (!respuesta.ok) {
       throw new Error("Error al consultar la API");
     }
     const datos = await respuesta.json();
     for (const dato of datos.carreras) {
       const elemento = document.createElement("li");
       const carrera = document.createElement("strong");
       carrera.textContent = dato.carrera + ": ";
       elemento.append(carrera, dato.idioma + ". " + dato.motivo); 
       lista.appendChild(elemento);
     }
     parecidos.textContent = datos.parecidos.join(", ") +
       " comparten raíces latinas con el español. " +
       "La pronunciación y la gramática cambian.";
   } catch {
     parecidos.textContent =
       "No se cargaron las sugerencias. Abre la página desde el servidor de Python.";
   }
 }
cargarIdiomas();
