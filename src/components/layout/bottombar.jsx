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
          <div className="col-md-12 text-center mb-4">
            <div className="d-block d-md-flex justify-content-center gap-3">
              <div>
                <div className="widget widget-links widget-light mb-2">
                  <a className="widget-list-link" href="mailto:info@janome.club">
                    <i className="ci-mail me-1"></i>
                    info@janome.club
                  </a>
                </div>
              </div>
              <div>
                <div className="fs-s text-light mb-2">Магазин на Автозаводской:</div>
                <div className="widget widget-links widget-light mb-2">
                  <a className="widget-list-link" href={"tel:" + "+74957844855"}>
                    <i className="ci-phone me-1"></i>
                    {formatPhone("+74957844855")}
                  </a>
                </div>
                <div className="fs-s text-light mb-2">Москва, Автозаводская ул., д.9/1</div>
              </div>
              {site.phone && (
                <div>
                  <div className="fs-s text-light mb-2">Интернет-магазин:</div>
                  <div className="widget widget-links widget-light mb-2">
                    <a className="widget-list-link" href={"tel:" + site.phone}>
                      <i className="ci-phone me-1"></i>
                      {formatPhone(site.phone)}
                    </a>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
        <div className="pb-1 fs-xs text-light text-center">
          <p>
            &copy; 2003-{new Date().getFullYear()} Janome. Все права защищены.{' '}
          </p>
          <p className="opacity-50">
            Developed by <a className="text-light" href="https://newf.ru/" target="_blank" rel="noopener">Andrey Novikov</a>.
            Design by <a className="text-light" href="https://createx.studio/" target="_blank" rel="noopener">Createx Studio</a>.
          </p>
        </div>
      </div>
    </footer >
  )
}
