import { EMPTY_FILTERS } from '../utils/filterTeas'

/** Подписи для bestTime в UI (значение в данных → текст кнопки) */
const BEST_TIME_LABELS = {
  Утро: 'Утро',
  День: 'День',
  'Ранний вечер': 'Вечер',
}

const EFFECT_ORDER = ['Взбодриться', 'Сфокусироваться', 'Согреться', 'Расслабиться']

function orderedValues(values, preferredOrder) {
  const set = new Set(values || [])
  const preferred = preferredOrder.filter((value) => set.has(value))
  const rest = [...set].filter((value) => !preferredOrder.includes(value)).sort((a, b) =>
    a.localeCompare(b, 'ru'),
  )
  return [...preferred, ...rest]
}

function MatrixChip({ label, active, onClick, count }) {
  return (
    <button
      type="button"
      className={`matrix-chip${active ? ' is-active' : ''}`}
      onClick={onClick}
      aria-pressed={active}
    >
      <span className="matrix-chip__label">{label}</span>
      {typeof count === 'number' ? (
        <span className="matrix-chip__count" aria-hidden="true">
          {count}
        </span>
      ) : null}
    </button>
  )
}

function MatrixRow({ title, children }) {
  return (
    <div className="selection-matrix__row">
      <p className="selection-matrix__row-title">{title}</p>
      <div className="selection-matrix__chips">{children}</div>
    </div>
  )
}

/**
 * Надстройка над фильтрами: быстрый подбор по осям из данных.
 * Пишет в те же filters, что и FilterPanel — каталог обновляется сразу.
 */
function SelectionMatrix({
  filters = EMPTY_FILTERS,
  options = {
    bestTimes: [],
    effects: [],
    taste: [],
    tasteCharacter: [],
  },
  matchCount = 0,
  onChange,
  searchSlot = null,
}) {
  const update = (patch) => {
    onChange?.({ ...filters, ...patch })
  }

  const toggleSingle = (key, value) => {
    const current = filters[key] || ''
    update({ [key]: current === value ? '' : value })
  }

  const toggleInList = (key, value) => {
    const selected = filters[key] || []
    const next = selected.includes(value)
      ? selected.filter((item) => item !== value)
      : [...selected, value]
    update({ [key]: next })
  }

  const hasMatrixSelection =
    Boolean(filters.bestTime) ||
    Boolean(filters.effect) ||
    (filters.taste || []).length > 0 ||
    (filters.tasteCharacter || []).length > 0

  const resetMatrixAxes = () => {
    onChange?.({
      ...filters,
      bestTime: '',
      effect: '',
      taste: [],
      tasteCharacter: [],
    })
  }

  return (
    <section className="panel selection-matrix" aria-label="Матрица выбора чая">
      <div className="selection-matrix__header">
        <div className="panel__heading">
          <h2 className="panel__title">Матрица выбора</h2>
        </div>
        <div className="selection-matrix__meta">
          <span className="panel__count" title="Подходящих чаёв">
            {matchCount}
          </span>
          <button
            type="button"
            className="btn btn--ghost"
            onClick={resetMatrixAxes}
            disabled={!hasMatrixSelection}
          >
            Сбросить подбор
          </button>
        </div>
      </div>

      {searchSlot ? <div className="selection-matrix__search">{searchSlot}</div> : null}

      <div className="selection-matrix__body">
        <MatrixRow title="Когда пить">
          {(options.bestTimes || []).map((value) => (
            <MatrixChip
              key={value}
              label={BEST_TIME_LABELS[value] || value}
              active={filters.bestTime === value}
              onClick={() => toggleSingle('bestTime', value)}
            />
          ))}
        </MatrixRow>

        <MatrixRow title="Задача">
          {orderedValues(options.effects, EFFECT_ORDER).map((value) => (
            <MatrixChip
              key={value}
              label={value}
              active={filters.effect === value}
              onClick={() => toggleSingle('effect', value)}
            />
          ))}
        </MatrixRow>

        <MatrixRow title="Вкус">
          {(options.taste || []).map((value) => (
            <MatrixChip
              key={value}
              label={value}
              active={(filters.taste || []).includes(value)}
              onClick={() => toggleInList('taste', value)}
            />
          ))}
        </MatrixRow>

        <MatrixRow title="Характер">
          {(options.tasteCharacter || []).map((value) => (
            <MatrixChip
              key={value}
              label={value}
              active={(filters.tasteCharacter || []).includes(value)}
              onClick={() => toggleInList('tasteCharacter', value)}
            />
          ))}
        </MatrixRow>
      </div>
    </section>
  )
}

export default SelectionMatrix
