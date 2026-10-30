function AiPromptBox() {
  return (
    <section className="panel ai-prompt-box" aria-label="AI-запрос">
      <div className="panel__heading">
        <h2 className="panel__title">AI-запрос</h2>
        <p className="panel__hint">Скоро</p>
      </div>
      <div className="empty-state empty-state--compact">
        <p className="empty-state__text">
          Свободный текстовый ввод через DeepSeek будет добавлен позже
        </p>
      </div>
    </section>
  )
}

export default AiPromptBox
