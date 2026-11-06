# Idiomas y tu futuro

Sitio informativo en español para orientar a estudiantes y personas que están
explorando cómo aprender otro idioma puede relacionarse con sus intereses,
estudios y metas profesionales.

## Archivos

- `index.html`: contenido y estructura semántica de la página.
- `front.css`: estilos adaptables para escritorio y dispositivos móviles.
- `assets/globo-terraqueo-multilingue.png`: imagen incluida localmente para que
  también se muestre en el sitio publicado.

## Ejecutar localmente

Abre `index.html` en un navegador. No se requieren dependencias ni un servidor.

## Publicar en GitHub Pages

El flujo `.github/workflows/pages.yml` publica el sitio al subir cambios a la
rama `main` y habilita GitHub Pages mediante GitHub Actions. El repositorio debe
permitir GitHub Actions y GitHub Pages en su configuración.

Después de subir el proyecto, revisa **Actions** para confirmar que el flujo
terminó correctamente. GitHub mostrará la URL activa en **Settings → Pages**.

El punto de entrada del sitio es `index.html`.
