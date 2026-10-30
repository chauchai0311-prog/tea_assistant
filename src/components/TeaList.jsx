import { getThermosFit } from '../utils/thermosFit'

function FeatureBadges({ tea }) {
  const thermosFit = getThermosFit(tea)

  return (
    <div className="badge-row">
      {tea.forThermos && (
        <span
          className={`badge badge--thermos${
            thermosFit === 'ideal' ? ' badge--thermos-ideal' : ''
          }`}
        >
          {thermosFit === 'ideal'
            ? 'Термос · идеально'
            : thermosFit === 'ok'
              ? 'Термос · допустимо'
              : 'Термос'}
        </span>
      )}
      {tea.forProliv && <span className="badge badge--proliv">Проливы</span>}
    </div>
  )
}

function TeaThumb({ tea }) {
  if (tea.image) {
    return (
      <img
        className="tea-list__thumb"
        src={tea.image}
        alt=""
        loading="lazy"
      />
    )
  }

  return <div className="tea-list__thumb tea-list__thumb--empty" aria-hidden="true" />
}

function TeaList({ teas = [], selectedTeaId = null, onSelectTea }) {
  return (
    <section className="panel tea-list" aria-label="Список чаев">
      <div className="panel__heading panel__heading--row">
        <h2 className="panel__title">Каталог</h2>
        <span className="panel__count">{teas.length}</span>
      </div>

      {teas.length === 0 ? (
        <div className="empty-state">
          <p className="empty-state__title">Ничего не найдено</p>
          <p className="empty-state__text">Попробуйте изменить поиск или сбросить фильтры</p>
        </div>
      ) : (
        <ul className="tea-list__items">
          {teas.map((tea) => {
            const isSelected = tea.id === selectedTeaId
            const previewTags = (tea.tags || []).slice(0, 3)

            return (
              <li key={tea.id}>
                <button
                  type="button"
                  className={`tea-list__item${isSelected ? ' is-selected' : ''}`}
                  onClick={() => onSelectTea?.(tea)}
                  aria-pressed={isSelected}
                >
                  <TeaThumb tea={tea} />

                  <div className="tea-list__body">
                    <div className="tea-list__item-top">
                      <span className="tea-list__name">{tea.name}</span>
                      <span className="tea-list__article">{tea.article}</span>
                    </div>

                    {tea.category && (
                      <div className="tea-list__meta">{tea.category}</div>
                    )}

                    <div className="tea-list__footer">
                      {previewTags.length > 0 && (
                        <div className="tag-row">
                          {previewTags.map((tag) => (
                            <span key={tag} className="tag">
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
                      <FeatureBadges tea={tea} />
                    </div>
                  </div>
                </button>
              </li>
            )
          })}
        </ul>
      )}
    </section>
  )
}

export default TeaList
