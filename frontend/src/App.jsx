import { useEffect, useState } from 'react'

import { obtenerGeneros, obtenerPelicula, obtenerRecomendaciones } from './api.js'
import MovieCard from './components/MovieCard.jsx'
import MovieDetail from './components/MovieDetail.jsx'

/**
 * Vista publica de recomendaciones - paso 10.
 *
 * Es el contraste con el panel que pide el enunciado: el panel es la vista
 * de back office (solo para quien tiene cuenta, para cargar y corregir datos,
 * y con la interfaz que impone Django). Esta pantalla es la vista publica
 * (para cualquiera, sin cuenta, para consultar, y con la interfaz que
 * decide este codigo).
 */
export default function App() {
  const [generos, setGeneros] = useState([])
  const [idGenero, setIdGenero] = useState('')
  const [peliculas, setPeliculas] = useState([])
  const [seleccionada, setSeleccionada] = useState(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState(null)

  // Los generos solo se piden una vez, para montar el selector.
  useEffect(() => {
    obtenerGeneros()
      .then(setGeneros)
      .catch((e) => setError(`No se pudieron cargar los generos: ${e.message}`))
  }, [])

  // Las recomendaciones se vuelven a pedir cada vez que cambia el genero.
  useEffect(() => {
    let vigente = true
    setCargando(true)
    obtenerRecomendaciones(idGenero)
      .then((datos) => {
        if (vigente) {
          setPeliculas(datos)
          setError(null)
        }
      })
      .catch((e) => vigente && setError(`No se pudieron cargar las peliculas: ${e.message}`))
      .finally(() => vigente && setCargando(false))

    return () => {
      vigente = false
    }
  }, [idGenero])

  async function abrirDetalle(id) {
    try {
      setSeleccionada(await obtenerPelicula(id))
    } catch (e) {
      setError(`No se pudo abrir la pelicula: ${e.message}`)
    }
  }

  return (
    <div className="app">
      <header className="cabecera">
        <h1>CineVault</h1>
        <p className="subtitulo">
          Peliculas del mismo genero mejor valoradas, ordenadas por la media de sus
          valoraciones.
        </p>
      </header>

      <main>
        <section className="filtros" aria-label="Filtrar por genero">
          <label htmlFor="selector-genero">Genero</label>
          <select
            id="selector-genero"
            value={idGenero}
            onChange={(e) => setIdGenero(e.target.value)}
          >
            <option value="">Todos los generos</option>
            {generos.map((g) => (
              <option key={g.id} value={g.id}>
                {g.name} ({g.movie_count})
              </option>
            ))}
          </select>
        </section>

        {error && <p className="error">{error}</p>}

        {cargando && <p className="cargando">Cargando peliculas...</p>}

        {!cargando && !error && peliculas.length === 0 && (
          <p className="vacio">
            Todavia no hay peliculas valoradas. Carga las desde el panel de
            administracion con <code>py manage.py seed_movies</code>.
          </p>
        )}

        <ul className="rejilla">
          {peliculas.map((p) => (
            <MovieCard key={p.id} pelicula={p} alElegir={() => abrirDetalle(p.id)} />
          ))}
        </ul>
      </main>

      {seleccionada && (
        <MovieDetail
          pelicula={seleccionada}
          alCerrar={() => setSeleccionada(null)}
        />
      )}

      <footer className="pie">
        <p>
          Datos de solo lectura desde la API de Django. Para anadir o corregir
          peliculas, entra en el panel de administracion.
        </p>
      </footer>
    </div>
  )
}
