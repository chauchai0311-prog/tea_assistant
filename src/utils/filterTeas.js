import { filterTeasBySearch } from './filterTeasBySearch'
import { collectTasteFilterOptions, splitTasteTags } from './tasteTaxonomy'

export const EMPTY_FILTERS = {
  category: '',
  effect: '',
  bestTime: '',
  taste: [],
  tasteCharacter: [],
  forThermos: false,
  forProliv: false,
}

/** Порядок «когда пить» для UI */
export const BEST_TIME_ORDER = ['Утро', 'День', 'Ранний вечер']

function uniqueSorted(values) {
  return [...new Set(values.filter(Boolean))].sort((a, b) =>
    String(a).localeCompare(String(b), 'ru'),
  )
}

/**
 * Опции фильтров, вычисленные из текущих данных.
 */
export function getFilterOptions(teas = []) {
  const tasteOptions = collectTasteFilterOptions(teas)

  const bestTimePresent = new Set(
    teas.flatMap((tea) => (Array.isArray(tea.bestTime) ? tea.bestTime : [])),
  )

  return {
    categories: uniqueSorted(teas.map((tea) => tea.category)),
    effects: uniqueSorted(teas.flatMap((tea) => tea.effect || [])),
    bestTimes: BEST_TIME_ORDER.filter((value) => bestTimePresent.has(value)),
    taste: tasteOptions.taste,
    tasteCharacter: tasteOptions.tasteCharacter,
  }
}

function hasAllValues(haystack, selected) {
  if (!selected.length) return true
  return selected.every((value) => haystack.includes(value))
}

function matchesFilters(tea, filters) {
  const {
    category = '',
    effect = '',
    bestTime = '',
    taste = [],
    tasteCharacter = [],
    forThermos = false,
    forProliv = false,
  } = filters || EMPTY_FILTERS

  if (category && tea.category !== category) {
    return false
  }

  if (effect) {
    const teaEffects = tea.effect || []
    if (!teaEffects.includes(effect)) {
      return false
    }
  }

  if (bestTime) {
    const teaTimes = Array.isArray(tea.bestTime) ? tea.bestTime : []
    if (!teaTimes.includes(bestTime)) {
      return false
    }
  }

  const split = splitTasteTags(tea.tags || [])

  if (!hasAllValues(split.taste, taste || [])) {
    return false
  }

  if (!hasAllValues(split.tasteCharacter, tasteCharacter || [])) {
    return false
  }

  if (forThermos && !tea.forThermos) {
    return false
  }

  if (forProliv && !tea.forProliv) {
    return false
  }

  return true
}

/**
 * Поиск + фильтры. Порядок: сначала search, затем filters.
 */
export function filterTeas(teas, { searchQuery = '', filters = EMPTY_FILTERS } = {}) {
  const bySearch = filterTeasBySearch(teas, searchQuery)
  return bySearch.filter((tea) => matchesFilters(tea, filters))
}
