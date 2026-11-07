'use client'

import { IconMail, IconPhone } from '@tabler/icons-react'

import { widgetLinkClass } from '@/components/ui/widget'

import { useSite } from '@/lib/site'
import { formatPhone } from '@/lib/format'

const captionClass = 'mb-2 text-white'
const linkIcon = { size: 16, stroke: 1.5, className: 'me-1 -mt-0.5 align-middle' }

export default function BottomBar() {
  const { site } = useSite()

  return (
    // below lg the handheld toolbar covers the bottom of the page
    <footer className="shrink-0 bg-dark pt-12 pb-14 lg:pb-0">
      <div className="container">
        <div className="pb-2">
          <div className="mb-6 justify-center gap-4 text-center md:flex">
            <div className="mb-2">
              <a className={widgetLinkClass({ light: true })} href="mailto:info@janome.club">
                <IconMail {...linkIcon} />
                info@janome.club
              </a>
            </div>
            <div>
              <div className={captionClass}>Магазин на Автозаводской:</div>
              <div className="mb-2">
                <a className={widgetLinkClass({ light: true })} href={"tel:" + "+74957844855"}>
                  <IconPhone {...linkIcon} />
                  {formatPhone("+74957844855")}
                </a>
              </div>
              <div className={captionClass}>Москва, Автозаводская ул., д.9/1</div>
            </div>
            {site.phone && (
              <div>
                <div className={captionClass}>Интернет-магазин:</div>
                <div className="mb-2">
                  <a className={widgetLinkClass({ light: true })} href={"tel:" + site.phone}>
                    <IconPhone {...linkIcon} />
                    {formatPhone(site.phone)}
                  </a>
                </div>
              </div>
            )}
          </div>
        </div>
        <div className="pb-1 text-center text-xs text-white">
          <p className="mb-4">
            &copy; 2003-{new Date().getFullYear()} Janome. Все права защищены.
          </p>
          <p className="mb-4 opacity-50">
            Developed by <a className="text-white" href="https://newf.ru/" target="_blank" rel="noopener">Andrey Novikov</a>.
            Design by <a className="text-white" href="https://createx.studio/" target="_blank" rel="noopener">Createx Studio</a>.
          </p>
        </div>
      </div>
    </footer>
  )
}
