/**
 * Уровни пригодности для термоса (из Excel, не только да/нет).
 *
 * ideal     — «Да. Идеально.»
 * yes       — «Да»
 * ok        — «Допустимо»
 * avoid     — «Не желательно»
 * no        — «Нет»
 * forbidden — «КАТЕГОРИЧЕСКИ НЕТ»
 */

export const THERMOS_FIT_SCORE = {
  ideal: 5,
  yes: 3,
  ok: 1,
  avoid: 0,
  no: 0,
  forbidden: 0,
  unknown: 0,
}

export const THERMOS_FIT_LABEL = {
  ideal: 'Идеально для термоса',
  yes: 'Подходит для термоса',
  ok: 'Допустимо для термоса',
  avoid: 'Нежелательно для термоса',
  no: 'Не для термоса',
  forbidden: 'Категорически не для термоса',
  unknown: 'Для термоса: нет данных',
}

export function getThermosFit(tea) {
  return tea?.thermosFit || (tea?.forThermos ? 'yes' : 'no')
}

export function getThermosDisplayLabel(tea) {
  if (tea?.thermosLabel) return tea.thermosLabel
  return THERMOS_FIT_LABEL[getThermosFit(tea)] || THERMOS_FIT_LABEL.unknown
}

/**
 * Текст для карточки чая: «Термос — Да. Идеально.» и т.п.
 */
export function getThermosCardLabel(tea) {
  const raw = String(tea?.thermosLabel || '').trim()
  if (raw) {
    return `Термос — ${raw}`
  }

  const fit = getThermosFit(tea)
  const fallback = {
    ideal: 'Да. Идеально.',
    yes: 'Да',
    ok: 'Допустимо',
    avoid: 'Не желательно',
    no: 'Нет',
    forbidden: 'КАТЕГОРИЧЕСКИ НЕТ',
    unknown: 'нет данных',
  }

  return `Термос — ${fallback[fit] || fallback.unknown}`
}
