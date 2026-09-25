/** Ficha de una pelicula en la rejilla de recomendaciones. */
export default function MovieCard({ pelicula, alElegir }) {
  const { title, year, average_score, ratings_count, genres } = pelicula

  return (
    <li className="tarjeta">
      <button type="button" className="tarjeta-boton" onClick={alElegir}>
        <h2>{title}</h2>
        <p className="anio">{year}</p>
        <p className="nota">
          <span className="media">{average_score?.toFixed(2) ?? '—'}</span>
          <span className="escala">/10</span>
          <span className="conteo">
            {ratings_count} {ratings_count === 1 ? 'valoración' : 'valoraciones'}
          </span>
        </p>
        <p className="generos">
          {genres.map((g) => g.name).join(' · ')}
        </p>
      </button>
    </li>
  )
}
