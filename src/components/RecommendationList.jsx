function PreviewTags({ tags = [] }) {
  const preview = tags.slice(0, 2)
  if (!preview.length) return null

  return (
    <div className="tag-row">
      {preview.map((tag) => (
        <span key={tag} className="tag">
          {tag}
        </span>
      ))}
    </div>
  )
}

function RecommendationCard({ item, variant = 'alternative', selected, onSelect }) {
  const { tea, explanation } = item
  const isPrimary = variant === 'primary'

  return (
    <button
      type="button"
      className={[
        'recommendation-card',
        isPrimary ? 'recommendation-card--primary' : 'recommendation-card--alt',
        selected ? 'is-selected' : '',
      ]
        .filter(Boolean)
        .join(' ')}
      onClick={() => onSelect?.(tea)}
      aria-pressed={selected}
    >
      <div className="recommendation-card__label-row">
        <span className={`recommendation-card__badge${isPrimary ? '' : ' recommendation-card__badge--alt'}`}>
          {isPrimary ? 'Лучший вариант' : 'Альтернатива'}
        </span>
        <span className="recommendation-card__article">{tea.article}</span>
      </div>

      <div className="recommendation-card__main">
        {tea.image ? (
          <img className="recommendation-card__thumb" src={tea.image} alt="" loading="lazy" />
        ) : (
          <div className="recommendation-card__thumb recommendation-card__thumb--empty" aria-hidden="true" />
        )}

        <div className="recommendation-card__content">
          <span className="recommendation-card__name">{tea.name}</span>
          <PreviewTags tags={tea.tags} />
          <p className="recommendation-card__explanation">{explanation}</p>
        </div>
      </div>
    </button>
  )
}

function RecommendationList({ recommendations = null, selectedTeaId = null, onSelectTea }) {
  const primary = recommendations?.primary ?? null
  const alternatives = recommendations?.alternatives ?? []
  const isEmpty = !primary

  return (
    <section className="panel recommendation-list" aria-label="Рекомендации">
      <div className="panel__heading">
        <h2 className="panel__title">Рекомендации</h2>
        <p className="panel__hint">На основе поиска и фильтров</p>
      </div>

      {isEmpty ? (
        <div className="empty-state">
          <p className="empty-state__title">Нет подходящих вариантов</p>
          <p className="empty-state__text">Измените поиск или фильтры, чтобы получить подбор</p>
        </div>
      ) : (
        <div className="recommendation-list__items">
          <RecommendationCard
            item={primary}
            variant="primary"
            selected={primary.tea.id === selectedTeaId}
            onSelect={onSelectTea}
          />

          {alternatives.length > 0 && (
            <div className="recommendation-list__alts">
              {alternatives.map((item) => (
                <RecommendationCard
                  key={item.tea.id}
                  item={item}
                  variant="alternative"
                  selected={item.tea.id === selectedTeaId}
                  onSelect={onSelectTea}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </section>
  )
}

export default RecommendationList
