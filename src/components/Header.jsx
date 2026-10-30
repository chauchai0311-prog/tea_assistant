import { LOGO_MAIN } from '../data/logoAssets'

function hideBrokenImage(event) {
  const img = event.currentTarget
  img.style.display = 'none'
  const fallback = img.nextElementSibling
  if (fallback) {
    fallback.hidden = false
  }
}

function Header() {
  return (
    <header className="header">
      <div className="header__inner">
        <div className="header__logo">
          <img
            className="header__logo-image"
            src={LOGO_MAIN}
            alt="чаю чай"
            onError={hideBrokenImage}
          />
          <span className="header__logo-fallback" hidden aria-hidden="true">
            чаю чай
          </span>
        </div>

        <div className="header__text">
          <h1 className="header__title">Помощник по чаю</h1>
          <p className="header__subtitle">Быстрый подбор чая для витрины</p>
        </div>
      </div>
    </header>
  )
}

export default Header
