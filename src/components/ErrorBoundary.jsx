import { Component } from 'react'

/**
 * Ловит ошибки рендера и показывает сообщение вместо белого экрана.
 */
class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { error: null }
  }

  static getDerivedStateFromError(error) {
    return { error }
  }

  render() {
    if (this.state.error) {
      return (
        <div className="error-boundary" role="alert">
          <h1 className="error-boundary__title">Ошибка интерфейса</h1>
          <p className="error-boundary__text">{this.state.error.message}</p>
          <button type="button" className="btn" onClick={() => window.location.reload()}>
            Обновить страницу
          </button>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
