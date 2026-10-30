/**
 * Фильтрация чаёв по частичному совпадению:
 * артикул, название, описание, вкус, аромат (без учёта регистра).
 */
export function filterTeasBySearch(teas, query) {
  const normalized = String(query ?? '').trim().toLowerCase()

  if (!normalized) {
    return teas
  }

  return teas.filter((tea) => {
    const article = String(tea.article ?? '').toLowerCase()
    const name = String(tea.name ?? '').toLowerCase()
    const description = String(tea.description ?? '').toLowerCase()
    const taste = (tea.taste || []).join(' ').toLowerCase()
    const aroma = (tea.aroma || []).join(' ').toLowerCase()

    return (
      article.includes(normalized) ||
      name.includes(normalized) ||
      description.includes(normalized) ||
      taste.includes(normalized) ||
      aroma.includes(normalized)
    )
  })
}
