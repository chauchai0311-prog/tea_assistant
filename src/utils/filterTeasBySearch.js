/**
 * Нормализация для поиска: регистр, ё→е, без ъ/ь
 * (чтобы «нефть» находило «нефтяной»).
 */
function normalizeSearchText(value) {
  return String(value ?? '')
    .toLowerCase()
    .replaceAll('ё', 'е')
    .replace(/[ъь]/g, '')
}

function fieldToText(value) {
  if (value == null) return ''
  if (Array.isArray(value)) return value.join(' ')
  return String(value)
}

/**
 * Собирает текст карточки, по которому ищем ключевые слова.
 */
function buildTeaSearchBlob(tea) {
  return normalizeSearchText(
    [
      tea.article,
      tea.name,
      tea.category,
      tea.teaClass,
      tea.description,
      fieldToText(tea.taste),
      fieldToText(tea.aroma),
      fieldToText(tea.effect),
      fieldToText(tea.effectDescription),
      fieldToText(tea.tags),
      fieldToText(tea.antiTags),
      fieldToText(tea.bestTime),
      tea.brewingGuide,
      tea.thermosLabel,
      tea.brewDose,
      tea.brewTemp,
      tea.brewTime,
      tea.brewSteeps,
    ].join(' '),
  )
}

/**
 * Фильтрация чаёв по частичному совпадению:
 * артикул, название и ключевые слова из карточки (описание, вкус, аромат, теги и т.д.).
 */
export function filterTeasBySearch(teas, query) {
  const normalized = normalizeSearchText(String(query ?? '').trim())

  if (!normalized) {
    return teas
  }

  return teas.filter((tea) => buildTeaSearchBlob(tea).includes(normalized))
}
