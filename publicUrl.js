/**
 * Путь к файлу из public/ с учётом Vite base
 * (нужно для GitHub Pages: /tea_assistant/...).
 */
export function publicUrl(path = '') {
  const base = import.meta.env.BASE_URL || '/'
  const normalized = String(path || '').replace(/^\/+/, '')
  return `${base}${normalized}`
}
