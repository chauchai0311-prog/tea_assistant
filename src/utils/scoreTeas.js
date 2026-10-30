import { buildTeaProseText, proseMentionsLabel } from './tasteProseMatch'
import { splitTasteTags } from './tasteTaxonomy'
import { getThermosFit, THERMOS_FIT_SCORE } from './thermosFit'

/**
 * Scoring рекомендаций по правилам (без AI).
 *
 * «Лучший вариант» = max score среди уже отфильтрованных чаёв.
 * Учитывает:
 * - теги вкуса / характера
 * - подтверждение в тексте description / taste / aroma (мягкий бонус)
 * - градацию термоса
 * - поиск по артикулу / названию / описанию
 */

export const SCORE_WEIGHTS = {
  effect: 3,
  bestTime: 2,
  taste: 2,
  tasteCharacter: 2,
  tasteProse: 1,
  tasteCharacterProse: 1,
  forProliv: 2,
  category: 2,
  articleExact: 5,
  articlePartial: 3,
  name: 2,
  description: 1,
}

/**
 * Считает score и список совпадений для одного чая.
 */
export function scoreTea(tea, { searchQuery = '', filters = {} } = {}) {
  const matches = []
  let score = 0

  const category = filters.category || ''
  const effect = filters.effect || ''
  const bestTime = filters.bestTime || ''
  const selectedTaste = filters.taste || []
  const selectedCharacter = filters.tasteCharacter || []
  const forThermos = Boolean(filters.forThermos)
  const forProliv = Boolean(filters.forProliv)

  const split = splitTasteTags(tea.tags || [])
  const proseText = buildTeaProseText(tea)

  if (effect && (tea.effect || []).includes(effect)) {
    score += SCORE_WEIGHTS.effect
    matches.push({ kind: 'effect', value: effect, points: SCORE_WEIGHTS.effect })
  }

  if (bestTime && (tea.bestTime || []).includes(bestTime)) {
    score += SCORE_WEIGHTS.bestTime
    matches.push({ kind: 'bestTime', value: bestTime, points: SCORE_WEIGHTS.bestTime })
  }

  for (const value of selectedTaste) {
    if (split.taste.includes(value)) {
      score += SCORE_WEIGHTS.taste
      matches.push({ kind: 'taste', value, points: SCORE_WEIGHTS.taste })
    }

    if (proseMentionsLabel(proseText, value)) {
      score += SCORE_WEIGHTS.tasteProse
      matches.push({
        kind: 'tasteProse',
        value,
        points: SCORE_WEIGHTS.tasteProse,
      })
    }
  }

  for (const value of selectedCharacter) {
    if (split.tasteCharacter.includes(value)) {
      score += SCORE_WEIGHTS.tasteCharacter
      matches.push({
        kind: 'tasteCharacter',
        value,
        points: SCORE_WEIGHTS.tasteCharacter,
      })
    }

    if (proseMentionsLabel(proseText, value)) {
      score += SCORE_WEIGHTS.tasteCharacterProse
      matches.push({
        kind: 'tasteCharacterProse',
        value,
        points: SCORE_WEIGHTS.tasteCharacterProse,
      })
    }
  }

  if (forThermos && tea.forThermos) {
    const fit = getThermosFit(tea)
    const points = THERMOS_FIT_SCORE[fit] ?? THERMOS_FIT_SCORE.yes
    score += points
    matches.push({ kind: 'thermos', value: fit, points })
  }

  if (forProliv && tea.forProliv) {
    score += SCORE_WEIGHTS.forProliv
    matches.push({ kind: 'proliv', points: SCORE_WEIGHTS.forProliv })
  }

  if (category && tea.category === category) {
    score += SCORE_WEIGHTS.category
    matches.push({ kind: 'category', value: category, points: SCORE_WEIGHTS.category })
  }

  const query = String(searchQuery ?? '').trim().toLowerCase()
  if (query) {
    const article = String(tea.article ?? '').toLowerCase()
    const name = String(tea.name ?? '').toLowerCase()
    const description = String(tea.description ?? '').toLowerCase()
    const taste = (tea.taste || []).join(' ').toLowerCase()
    const aroma = (tea.aroma || []).join(' ').toLowerCase()

    if (article === query) {
      score += SCORE_WEIGHTS.articleExact
      matches.push({
        kind: 'articleExact',
        value: tea.article,
        points: SCORE_WEIGHTS.articleExact,
      })
    } else if (article.includes(query)) {
      score += SCORE_WEIGHTS.articlePartial
      matches.push({
        kind: 'articlePartial',
        value: tea.article,
        points: SCORE_WEIGHTS.articlePartial,
      })
    }

    if (name.includes(query)) {
      score += SCORE_WEIGHTS.name
      matches.push({ kind: 'name', value: query, points: SCORE_WEIGHTS.name })
    }

    if (
      description.includes(query) ||
      taste.includes(query) ||
      aroma.includes(query)
    ) {
      score += SCORE_WEIGHTS.description
      matches.push({ kind: 'description', value: query, points: SCORE_WEIGHTS.description })
    }
  }

  return { score, matches }
}

/**
 * Сортирует текущую выдачу по score и возвращает топ для рекомендаций.
 */
export function rankTeasForRecommendations(
  teas,
  { searchQuery = '', filters = {}, limit = 3 } = {},
) {
  return teas
    .map((tea) => {
      const { score, matches } = scoreTea(tea, { searchQuery, filters })
      return { tea, score, matches }
    })
    .sort((a, b) => {
      if (b.score !== a.score) return b.score - a.score
      return String(a.tea.name || '').localeCompare(String(b.tea.name || ''), 'ru')
    })
    .slice(0, limit)
}
