/**
 * Собирает короткое объяснение из совпадений scoring.
 */

function quote(value) {
  return `«${value}»`
}

function formatList(values) {
  if (values.length === 1) return quote(values[0])
  if (values.length === 2) return `${quote(values[0])} и ${quote(values[1])}`
  const head = values.slice(0, -1).map(quote).join(', ')
  return `${head} и ${quote(values[values.length - 1])}`
}

/**
 * @param {Array<{ kind: string, value?: string }>} matches
 */
export function buildRecommendationExplanation(matches = []) {
  if (!matches.length) {
    return 'Подходит под текущую выборку'
  }

  const parts = []

  const effects = matches.filter((m) => m.kind === 'effect').map((m) => m.value)
  if (effects.length) {
    parts.push(`эффекту ${formatList(effects)}`)
  }

  const tastes = [
    ...new Set([
      ...matches.filter((m) => m.kind === 'taste').map((m) => m.value),
      ...matches.filter((m) => m.kind === 'tasteProse').map((m) => m.value),
    ]),
  ]
  if (tastes.length) {
    const fromProse = matches.some((m) => m.kind === 'tasteProse')
    parts.push(
      fromProse
        ? `вкусу ${formatList(tastes)} (в т.ч. по описанию)`
        : `вкусу ${formatList(tastes)}`,
    )
  }

  const characters = [
    ...new Set([
      ...matches.filter((m) => m.kind === 'tasteCharacter').map((m) => m.value),
      ...matches.filter((m) => m.kind === 'tasteCharacterProse').map((m) => m.value),
    ]),
  ]
  if (characters.length) {
    const fromProse = matches.some((m) => m.kind === 'tasteCharacterProse')
    parts.push(
      fromProse
        ? `характеру вкуса ${formatList(characters)} (в т.ч. по описанию)`
        : `характеру вкуса ${formatList(characters)}`,
    )
  }

  const thermos = matches.find((m) => m.kind === 'thermos')
  if (thermos) {
    if (thermos.value === 'ideal') {
      parts.push('тому, что идеально подходит для термоса')
    } else if (thermos.value === 'ok') {
      parts.push('тому, что допустим для термоса')
    } else {
      parts.push('выбору для термоса')
    }
  }

  if (matches.some((m) => m.kind === 'proliv')) {
    parts.push('выбору для проливов')
  }

  const categories = matches.filter((m) => m.kind === 'category').map((m) => m.value)
  if (categories.length) {
    parts.push(`категории ${formatList(categories)}`)
  }

  if (matches.some((m) => m.kind === 'articleExact')) {
    parts.push('точному артикулу')
  } else if (matches.some((m) => m.kind === 'articlePartial')) {
    parts.push('артикулу')
  }

  if (matches.some((m) => m.kind === 'name')) {
    parts.push('названию')
  }

  if (matches.some((m) => m.kind === 'description')) {
    parts.push('описанию вкуса')
  }

  if (!parts.length) {
    return 'Подходит под текущую выборку'
  }

  if (parts.length === 1) {
    return `Подходит по ${parts[0]}`
  }

  if (parts.length === 2) {
    return `Подходит по ${parts[0]} и ${parts[1]}`
  }

  const last = parts[parts.length - 1]
  const head = parts.slice(0, -1).join(', ')
  return `Подходит по ${head} и ${last}`
}
