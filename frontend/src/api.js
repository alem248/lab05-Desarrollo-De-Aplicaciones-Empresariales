/**
 * Cliente de la API de Django.
 *
 * El backend corre en el 8000 y se declara en CORS_ALLOWED_ORIGINS
 * (backend/cinevault/settings.py). La SPA es de solo lectura: aquí no hay
 * ninguna función de escritura, el alta de datos se hace en el panel.
 */

const BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api'

/** Lanza un error con el detalle que devuelve Django, no un 500 genérico. */
async function pedir(ruta) {
  const respuesta = await fetch(`${BASE}${ruta}`)

  if (!respuesta.ok) {
    let detalle = `Error ${respuesta.status}`
    try {
      const cuerpo = await respuesta.json()
      if (cuerpo.detail) detalle = cuerpo.detail
    } catch {
      // La respuesta no era JSON; nos quedamos con el codigo HTTP.
    }
    throw new Error(detalle)
  }

  return respuesta.json()
}

/** DRF pagina sus listados: los resultados van en `results`. */
function resultados(cuerpo) {
  return Array.isArray(cuerpo) ? cuerpo : (cuerpo?.results ?? [])
}

/** Los cuatro generos del panel, para el selector. */
export async function obtenerGeneros() {
  return resultados(await pedir('/genres/'))
}

/**
 * Paso 10: peliculas del mismo genero mejor valoradas.
 * Sin `idGenero` devuelve todas las peliculas valoradas por media.
 */
export async function obtenerRecomendaciones(idGenero) {
  const consulta = idGenero ? `?genre=${encodeURIComponent(idGenero)}` : ''
  return resultados(await pedir(`/recomendaciones/${consulta}`))
}

/** Detalle de una pelicula, con su reparto y sus valoraciones. */
export async function obtenerPelicula(id) {
  return pedir(`/movies/${id}/`)
}
