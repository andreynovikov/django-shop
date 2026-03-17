import Link from 'next/link'

import DzenIcon from '@/assets/icons/social/dzen'

import { useSite } from '@/lib/site'
import { formatPhone } from '@/lib/format'

export default function BottomBar() {
  const { site } = useSite()

  return (
    <footer className="footer bg-dark pt-5">
      <div className="container">
        <div className="row pb-2">
          <div className="col-md-6 text-center text-md-start mb-4">
            <div className="widget widget-links widget-light">
              <ul className="widget-list d-flex flex-wrap justify-content-center justify-content-md-start">
                { /* <li class="nav-item"><a class="nav-link" href="{% url 'sales_actions' %}">Акции</a></li> */}
                <li className="widget-list-item me-4">
                  <Link className="widget-list-link" href="/pages/articles/">
                    Справочные материалы
                  </Link>
                </li>
                <li className="widget-list-item me-4">
                  <Link className="widget-list-link" href="/blog/entries">
                    Блог
                  </Link>
                </li>
              </ul>
            </div>

          </div>
          <div className="col-md-6 text-center text-md-end mb-4">
            <div className="widget widget-links widget-light mb-2">
              <a className="widget-list-link" href="mailto:info@thsm.ru">
                <i className="ci-mail me-1"></i>
                info@thsm.ru
              </a>
            </div>
            <div className="d-block d-md-flex justify-content-md-end gap-3">
            {site.phone && (
              <div>
                <div className="fs-xs text-light opacity-50 mb-2">Интернет-магазин:</div>
                <div className="widget widget-links widget-light mb-2">
                  <a className="widget-list-link" href={"tel:" + site.phone}>
                    <i className="ci-phone me-1"></i>
                    {formatPhone(site.phone)}
                  </a>
                </div>
              </div>
            )}
              <div>
                <div className="fs-xs text-light opacity-50 mb-2">Розничные магазины:</div>
                <div className="widget widget-links widget-light mb-2">
                  <a className="widget-list-link" href={"tel:" + "+74957440087"}>
                    <i className="ci-phone me-1"></i>
                    {formatPhone("+74957440087")}
                  </a>
                </div>
              </div>
              </div>
            <div className="fs-xs text-light opacity-50 mb-2">Наши страницы в соцсетях:</div>
            <div className="d-flex justify-content-center justify-content-md-end gap-2 mb-2">
              <a className="btn-social bs-outline bs-light bs-vk" href="https://vk.com/sew.world">
                <i className="ci-vk"></i>
              </a>
              <a className="btn-social bs-outline bs-light bs-dzen d-block align-content-center" href="https://shorturl.at/ZzJbf">
                <DzenIcon className="align-baseline" />
              </a>
              <a className="btn-social bs-outline bs-light bs-telegram" href="https://t.me/sewingworldrus">
                <i className="ci-telegram"></i>
              </a>
              <a className="btn-social bs-outline bs-light bs-youtube" href="https://youtube.com/%D0%A8%D0%B2%D0%B5%D0%B9%D0%BD%D1%8B%D0%B9%D0%9C%D0%B8%D1%80%D0%A0%D0%BE%D1%81%D1%81%D0%B8%D1%8F">
                <i className="ci-youtube"></i>
              </a>
            </div>
            <div className="fs-xs text-light opacity-50 mb-3">Присоединяйтесь!</div>
          </div>
        </div>
        <div className="pb-4 fs-xs text-light opacity-50 text-center text-md-start">
          &copy; 2003-{new Date().getFullYear()} Швейный Мир. Все права защищены.{' '}
          <span className="opacity-50">
            Developed by <a className="text-light" href="https://newf.ru/" target="_blank" rel="noopener">Andrey Novikov</a>.
            Design by <a className="text-light" href="https://createx.studio/" target="_blank" rel="noopener">Createx Studio</a>.
          </span>
        </div>
      </div>
    </footer >
  )
}
