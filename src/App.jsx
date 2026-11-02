import { useEffect, useMemo, useRef, useState } from 'react'
import Header from './components/Header'
import SearchBar from './components/SearchBar'
import FilterPanel from './components/FilterPanel'
import AiPromptBox from './components/AiPromptBox'
import SelectionMatrix from './components/SelectionMatrix'
import RecommendationList from './components/RecommendationList'
import TeaDetails from './components/TeaDetails'
import TeaList from './components/TeaList'
import { ENABLE_AI_ASSISTANT, ENABLE_SELECTION_MATRIX } from './config/featureFlags'
import { fetchTeas } from './services/teaService'
import { buildRecommendations } from './utils/buildRecommendations'
import { EMPTY_FILTERS, filterTeas, getFilterOptions } from './utils/filterTeas'

function App() {
  const [teas, setTeas] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedTea, setSelectedTea] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [filters, setFilters] = useState(() => ({
    ...EMPTY_FILTERS,
    taste: [],
    tasteCharacter: [],
  }))
  const detailsRef = useRef(null)
  const resultsRef = useRef(null)

  useEffect(() => {
    let cancelled = false

    async function loadTeas() {
      setLoading(true)
      setError(null)

      try {
        const data = await fetchTeas()
        if (!cancelled) {
          setTeas(data)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Ошибка загрузки данных')
          setTeas([])
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    loadTeas()

    return () => {
      cancelled = true
    }
  }, [])

  const filterOptions = useMemo(() => getFilterOptions(teas), [teas])

  const filteredTeas = useMemo(
    () => filterTeas(teas, { searchQuery, filters }),
    [teas, searchQuery, filters],
  )

  const visibleSelectedTea = useMemo(() => {
    if (!selectedTea) return null
    return filteredTeas.some((tea) => tea.id === selectedTea.id) ? selectedTea : null
  }, [selectedTea, filteredTeas])

  const recommendations = useMemo(
    () => buildRecommendations(filteredTeas, { searchQuery, filters }),
    [filteredTeas, searchQuery, filters],
  )

  const scrollToResults = () => {
    requestAnimationFrame(() => {
      resultsRef.current?.scrollIntoView({
        behavior: 'smooth',
        block: 'start',
      })
    })
  }

  const handleSelectTea = (tea) => {
    setSelectedTea(tea)
    requestAnimationFrame(() => {
      detailsRef.current?.scrollIntoView({
        behavior: 'smooth',
        block: 'start',
      })
    })
  }

  const searchBar = (
    <SearchBar
      value={searchQuery}
      onChange={setSearchQuery}
      onSubmit={scrollToResults}
      resultCount={loading || error ? null : filteredTeas.length}
      onJumpToResults={scrollToResults}
      variant={ENABLE_SELECTION_MATRIX ? 'embedded' : 'panel'}
    />
  )

  return (
    <div className="app">
      <Header />

      <main className="app__main">
        <aside className="app__controls" aria-label="Поиск и фильтры">
          <div className="controls-stack">
            {ENABLE_SELECTION_MATRIX ? (
              <SelectionMatrix
                filters={filters}
                options={filterOptions}
                matchCount={filteredTeas.length}
                onChange={setFilters}
                searchSlot={searchBar}
              />
            ) : (
              searchBar
            )}
            <FilterPanel
              filters={filters}
              options={filterOptions}
              onChange={setFilters}
            />
          </div>
          {ENABLE_AI_ASSISTANT ? <AiPromptBox /> : null}
        </aside>

        <section className="app__content" ref={resultsRef}>
          {loading && (
            <div className="status-message" role="status">
              <span className="status-message__spinner" aria-hidden="true" />
              <div>
                <p className="status-message__title">Загрузка каталога</p>
                <p className="status-message__text">Подготавливаем карточки чаёв…</p>
              </div>
            </div>
          )}

          {!loading && error && (
            <div className="status-message status-message--error" role="alert">
              <div>
                <p className="status-message__title">Не удалось загрузить данные</p>
                <p className="status-message__text">{error}</p>
              </div>
            </div>
          )}

          {!loading && !error && (
            <>
              <RecommendationList
                recommendations={recommendations}
                selectedTeaId={visibleSelectedTea?.id ?? null}
                onSelectTea={handleSelectTea}
              />
              <div ref={detailsRef} className="tea-details-anchor">
                <TeaDetails
                  tea={visibleSelectedTea}
                  onClear={() => setSelectedTea(null)}
                />
              </div>
              <TeaList
                teas={filteredTeas}
                selectedTeaId={visibleSelectedTea?.id ?? null}
                onSelectTea={handleSelectTea}
              />
            </>
          )}
        </section>
      </main>
    </div>
  )
}

export default App
