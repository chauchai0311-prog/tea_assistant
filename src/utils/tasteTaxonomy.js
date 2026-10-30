/**
 * Словари для разделения вкусовых тегов на 2 фильтра.
 * В данных сейчас это лежит в tea.tags — нормализуем на клиенте.
 */

/** Вкус — профильные ноты */
export const TASTE_FLAVORS = [
  'Древесно-землистый',
  'Минеральный',
  'Освежающий',
  'Ореховый',
  'Сливочный',
  'Карамельный',
  'Сухофруктовый',
  'Фруктовый',
  'Цветочный',
  'Медовый',
  'Шоколадный',
]

/** Характер вкуса — текстура / интенсивность */
export const TASTE_CHARACTERS = [
  'Мягкий',
  'Плотный',
  'Спокойный',
  'Терпкий',
  'Яркий',
  'Сладковатый',
]

const FLAVOR_SET = new Set(TASTE_FLAVORS)
const CHARACTER_SET = new Set(TASTE_CHARACTERS)

/**
 * Разбивает массив тегов чая на вкус / характер / нераспознанные.
 */
export function splitTasteTags(tags = []) {
  const taste = []
  const tasteCharacter = []
  const unmatched = []

  for (const tag of tags) {
    if (!tag) continue
    if (FLAVOR_SET.has(tag)) {
      taste.push(tag)
    } else if (CHARACTER_SET.has(tag)) {
      tasteCharacter.push(tag)
    } else {
      unmatched.push(tag)
    }
  }

  return { taste, tasteCharacter, unmatched }
}

/**
 * Собирает опции фильтров из реальных данных + фиксированных словарей.
 * Показываем только значения, которые встречаются хотя бы у одного чая.
 */
export function collectTasteFilterOptions(teas = []) {
  const flavorPresent = new Set()
  const characterPresent = new Set()
  const unmatchedPresent = new Set()

  for (const tea of teas) {
    const split = splitTasteTags(tea.tags || [])
    split.taste.forEach((value) => flavorPresent.add(value))
    split.tasteCharacter.forEach((value) => characterPresent.add(value))
    split.unmatched.forEach((value) => unmatchedPresent.add(value))
  }

  const byRu = (a, b) => a.localeCompare(b, 'ru')

  return {
    taste: TASTE_FLAVORS.filter((value) => flavorPresent.has(value)).sort(byRu),
    tasteCharacter: TASTE_CHARACTERS.filter((value) => characterPresent.has(value)).sort(byRu),
    unmatched: [...unmatchedPresent].sort(byRu),
  }
}
