import { EMPTY_FILTERS } from '../utils/filterTeas'

/**
 * Уточняющие фильтры каталога.
 * Вкус / характер / эффект / время — в SelectionMatrix, без дублей.
 */
function FilterPanel({
  filters = EMPTY_FILTERS,
  options = { categories: [] },
  onChange,
}) {
  const update = (patch) => {
    onChange?.({ ...filters, ...patch })
  }

  const hasActiveFilters =
    Boolean(filters.category) ||
    Boolean(filters.forThermos) ||
    Boolean(filters.forProliv)

  const resetPanelFilters = () => {
    onChange?.({
      ...filters,
      category: '',
      forThermos: false,
      forProliv: false,
    })
  }

  return (
    <section className="panel filter-panel" aria-label="Фильтры">
      <div className="filter-panel__header">
        <div className="panel__heading">
          <h2 className="panel__title">Фильтры</h2>
          <p className="panel__hint">Вид чая и способ заваривания</p>
        </div>
        <button
          type="button"
          className="btn btn--ghost"
          onClick={resetPanelFilters}
          disabled={!hasActiveFilters}
        >
          Сбросить фильтры
        </button>
      </div>

      <div className="filter-panel__fields">
        <label className="filter-field">
          <span className="filter-field__label">Вид чая</span>
          <select
            className="filter-field__control"
            value={filters.category || ''}
            onChange={(event) => update({ category: event.target.value })}
          >
            <option value="">Все виды</option>
            {(options.categories || []).map((category) => (
              <option key={category} value={category}>
                {category}
              </option>
            ))}
          </select>
        </label>

        <div className="filter-checks">
          <label className="filter-check">
            <input
              type="checkbox"
              checked={Boolean(filters.forThermos)}
              onChange={(event) => update({ forThermos: event.target.checked })}
            />
            <span>Подходит для термоса</span>
          </label>

          <label className="filter-check">
            <input
              type="checkbox"
              checked={Boolean(filters.forProliv)}
              onChange={(event) => update({ forProliv: event.target.checked })}
            />
            <span>Подходит для проливов</span>
          </label>
        </div>
      </div>
    </section>
  )
}

export default FilterPanel
