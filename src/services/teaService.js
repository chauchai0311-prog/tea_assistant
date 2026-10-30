/**
 * Загрузка каталога чаёв из public/teas.json
 */
export async function fetchTeas() {
  const response = await fetch('/teas.json')

  if (!response.ok) {
    throw new Error(`Не удалось загрузить данные чаёв (${response.status})`)
  }

  const data = await response.json()

  if (!Array.isArray(data)) {
    throw new Error('Некорректный формат teas.json: ожидался массив')
  }

  return data
}
