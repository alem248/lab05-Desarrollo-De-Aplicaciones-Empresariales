/**
 * Detalle de una pelicula: sinopsis, reparto y sus valoraciones.
 *
 * Usa el endpoint /api/movies/<id>/, que devuelve la pelicula completa, a
 * diferencia del listado de recomendaciones.
 */
export default function MovieDetail({ pelicula, alCerrar }) {
  const { title, year, summary, genres, people, ratings, average_score } = pelicula

  return (
    <div
      className="detalle-fondo"
      role="dialog"
      aria-modal="true"
      aria-label={title}
      onClick={alCerrar}
    >
      <article className="detalle" onClick={(e) => e.stopPropagation()}>
        <button type="button" className="cerrar" onClick={alCerrar} aria-label="Cerrar">
          ×
        </button>

        <h2>{title}</h2>
        <p className="anio">
          {year} · {average_score?.toFixed(2) ?? '—'}/10
        </p>

        {summary && <p className="sinopsis">{summary}</p>}

        <p className="generos">{genres.map((g) => g.name).join(' · ')}</p>

        {people.length > 0 && (
          <section>
            <h3>Reparto y equipo</h3>
            <ul className="lista-simple">
              {people.map((p) => (
                <li key={p.id}>{p.name}</li>
              ))}
            </ul>
          </section>
        )}

        <section>
          <h3>Valoraciones</h3>
          {ratings.length === 0 ? (
            <p className="vacio">Esta pelicula todavia no tiene valoraciones.</p>
          ) : (
            <ul className="lista-simple">
              {ratings.map((r) => (
                <li key={r.id}>
                  <strong>{r.score}/10</strong>
                  {r.author && <em> — {r.author}</em>}
                  {r.comment && <span> «{r.comment}»</span>}
                </li>
              ))}
            </ul>
          )}
        </section>
      </article>
    </div>
  )
}
