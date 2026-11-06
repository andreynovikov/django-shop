import { navbarClass, navbarContentClass, navLinkClass, navLinksClass } from '@/components/ui/navbar'

export default function Footer() {
  return (
    <footer className="container">
      <nav className={`${navbarClass} mb-2`}>
        <div className={navbarContentClass}>
          <div className={navLinksClass}>
            <a className={navLinkClass} href="http://www.dor-tak.com">&copy;2002-2023 Dor Tak Thread Manufacturing Ltd.</a>
            <a className={navLinkClass} href="http://www.sewing-world.ru">Представитель в России - &laquo;Швейный Мир&raquo;</a>
            <a className={navLinkClass} href="mailto:info@dor-tak.ru">info@dor-tak.ru</a>
            <a className={navLinkClass} href="tel:+74957665675">+7 495 766-56-75</a>
          </div>
        </div>
      </nav>
    </footer>
  )
}
