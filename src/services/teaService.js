import { publicUrl } from '../utils/publicUrl'

/**
 * Загрузка каталога чаёв из public/teas.json
 */
export async function fetchTeas() {
  const response = await fetch(publicUrl('teas.json'))

  if (!response.ok) {
    throw new Error(`Не удалось загрузить данные чаёв (${response.status})`)
  }

  const data = await response.json()

  if (!Array.isArray(data)) {
    throw new Error('Некорректный формат teas.json: ожидался массив')
  }

  // Картинки в JSON вида /images/tea/... — на GitHub Pages нужен base-префикс
  return data.map((tea) => ({
    ...tea,
    image: tea.image ? publicUrl(tea.image) : tea.image,
  }))
}
