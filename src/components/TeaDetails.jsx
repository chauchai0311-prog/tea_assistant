import { getThermosCardLabel, getThermosFit } from '../utils/thermosFit'
import { splitTasteTags } from '../utils/tasteTaxonomy'

function joinList(value) {
  if (!value) return ''
  if (Array.isArray(value)) return value.filter(Boolean).join(', ')
  return String(value)
}

function DetailBlock({ label, children }) {
  if (children === null || children === undefined || children === false || children === '') {
    return null
  }

  return (
    <div className="detail-block">
      <h4 className="detail-block__label">{label}</h4>
      <div className="detail-block__body">{children}</div>
    </div>
  )
}

function TagList({ items }) {
  if (!items || items.length === 0) return null

  return (
    <div className="tag-row">
      {items.map((item) => (
        <span key={item} className="tag">
          {item}
        </span>
      ))}
    </div>
  )
}

function TeaDetails({ tea = null, onClear }) {
  const tasteSplit = tea ? splitTasteTags(tea.tags || []) : null

  return (
    <section
      className={`panel tea-details${tea ? ' tea-details--active' : ''}`}
      aria-label="Карточка чая"
    >
      <div className="panel__heading panel__heading--row">
        <div>
          <h2 className="panel__title">Карточка чая</h2>
          <p className="panel__hint">
            {tea ? 'Выбранная позиция' : 'Выберите чай в рекомендациях или каталоге'}
          </p>
        </div>
        {tea ? (
          <button type="button" className="btn btn--ghost" onClick={() => onClear?.()}>
            Сбросить
          </button>
        ) : null}
      </div>

      {!tea ? (
        <div className="empty-state empty-state--compact">
          <p className="empty-state__text">
            Карточка откроется здесь — над каталогом, без прокрутки вниз
          </p>
        </div>
      ) : (
        <article className="product-card">
          <div className="product-card__media">
            {tea.image ? (
              <img
                className="product-card__image"
                src={tea.image}
                alt={tea.name}
                loading="lazy"
              />
            ) : (
              <div className="product-card__image-placeholder" aria-hidden="true">
                Нет фото
              </div>
            )}
          </div>

          <div className="product-card__header">
            <div className="badge-row">
              {tea.category ? <span className="badge">{tea.category}</span> : null}
              {tea.teaClass ? <span className="badge badge--soft">{tea.teaClass}</span> : null}
            </div>

            <h3 className="product-card__name">{tea.name}</h3>
            {tea.article ? <p className="product-card__article">{tea.article}</p> : null}

            <div className="badge-row">
              <span
                className={`badge ${
                  tea.forThermos
                    ? getThermosFit(tea) === 'ideal'
                      ? 'badge--thermos badge--thermos-ideal'
                      : 'badge--thermos'
                    : 'badge--muted'
                }`}
              >
                {getThermosCardLabel(tea)}
              </span>
              {tea.forProliv ? (
                <span className="badge badge--proliv">Подходит для проливов</span>
              ) : (
                <span className="badge badge--muted">Не для проливов</span>
              )}
            </div>
          </div>

          <div className="product-card__sections">
            <DetailBlock label="Описание">
              {tea.description || null}
            </DetailBlock>

            <DetailBlock label="Вкус">
              {joinList(tea.taste) || null}
            </DetailBlock>

            <DetailBlock label="Аромат">
              {joinList(tea.aroma) || null}
            </DetailBlock>

            <DetailBlock label="Эффект">
              {tea.effectDescription || (tea.effect && tea.effect.length > 0) ? (
                <>
                  {tea.effectDescription ? (
                    <p className="product-card__paragraph">{tea.effectDescription}</p>
                  ) : null}
                  <TagList items={tea.effect} />
                </>
              ) : null}
            </DetailBlock>

            <DetailBlock label="Когда пить">
              {joinList(tea.bestTime) || null}
            </DetailBlock>

            <DetailBlock label="Правила заваривания">
              {tea.brewingGuide ? (
                <pre className="product-card__brewing">{tea.brewingGuide}</pre>
              ) : null}
            </DetailBlock>

            <DetailBlock label="Основные оттенки вкуса">
              {tasteSplit?.taste?.length ? <TagList items={tasteSplit.taste} /> : null}
            </DetailBlock>

            <DetailBlock label="Характер вкуса">
              {tasteSplit?.tasteCharacter?.length ? (
                <TagList items={tasteSplit.tasteCharacter} />
              ) : null}
            </DetailBlock>
          </div>
        </article>
      )}
    </section>
  )
}

export default TeaDetails
