function SearchBar({ value = '', onChange }) {
  return (
    <section className="panel search-bar" aria-label="Поиск">
      <div className="panel__heading">
        <h2 className="panel__title">Поиск</h2>
        <p className="panel__hint">Артикул или название</p>
      </div>

      <label className="search-bar__label" htmlFor="tea-search">
        <span className="visually-hidden">Поиск по названию или артикулу</span>
        <input
          id="tea-search"
          className="search-bar__input"
          type="search"
          value={value}
          onChange={(event) => onChange?.(event.target.value)}
          placeholder="Поиск по названию или артикулу"
          autoComplete="off"
          spellCheck="false"
        />
      </label>
    </section>
  )
}

export default SearchBar
