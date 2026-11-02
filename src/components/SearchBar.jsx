/**
 * @param {'panel' | 'embedded'} variant
 *   panel — отдельный блок; embedded — только поле (внутри матрицы)
 */
function SearchBar({
  value = '',
  onChange,
  onSubmit,
  resultCount = null,
  onJumpToResults,
  variant = 'panel',
}) {
  const query = String(value || '').trim()
  const showJump =
    Boolean(query) && typeof resultCount === 'number' && typeof onJumpToResults === 'function'

  const handleKeyDown = (event) => {
    if (event.key === 'Enter') {
      event.preventDefault()
      onSubmit?.(value)
    }
  }

  const field = (
    <>
      <label className="search-bar__label" htmlFor="tea-search">
        <span className="visually-hidden">
          Поиск по артикулу, названию или слову из карточки
        </span>
        <input
          id="tea-search"
          className="search-bar__input"
          type="search"
          value={value}
          onChange={(event) => onChange?.(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Артикул, название или слово (например, нефть)"
          autoComplete="off"
          spellCheck="false"
          enterKeyHint="search"
        />
      </label>

      {showJump ? (
        <button
          type="button"
          className="search-bar__jump"
          onClick={() => onJumpToResults?.()}
        >
          <span className="search-bar__jump-text">
            {resultCount === 0 ? 'Ничего не найдено' : `Найдено: ${resultCount}`}
          </span>
          {resultCount > 0 ? (
            <span className="search-bar__jump-action">Смотреть ↓</span>
          ) : null}
        </button>
      ) : null}
    </>
  )

  if (variant === 'embedded') {
    return (
      <div className="search-bar search-bar--embedded" aria-label="Поиск">
        {field}
      </div>
    )
  }

  return (
    <section className="panel search-bar" aria-label="Поиск">
      <div className="panel__heading">
        <h2 className="panel__title">Поиск</h2>
        <p className="panel__hint">Артикул или название</p>
      </div>
      {field}
    </section>
  )
}

export default SearchBar
