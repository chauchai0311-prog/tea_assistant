import { buildRecommendationExplanation } from './buildRecommendationExplanation'
import { rankTeasForRecommendations } from './scoreTeas'

/**
 * Готовит основную рекомендацию и до 2 альтернатив из уже отфильтрованной выдачи.
 */
export function buildRecommendations(filteredTeas, { searchQuery = '', filters = {} } = {}) {
  if (!filteredTeas.length) {
    return { primary: null, alternatives: [] }
  }

  const ranked = rankTeasForRecommendations(filteredTeas, {
    searchQuery,
    filters,
    limit: 3,
  })

  const toItem = (entry) => ({
    tea: entry.tea,
    score: entry.score,
    matches: entry.matches,
    explanation: buildRecommendationExplanation(entry.matches),
  })

  const [best, ...rest] = ranked

  return {
    primary: toItem(best),
    alternatives: rest.map(toItem),
  }
}
