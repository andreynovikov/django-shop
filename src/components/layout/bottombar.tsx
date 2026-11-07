'use client'

import Link from 'next/link'
import { IconBrandTelegram, IconBrandVk, IconBrandYoutubeFilled, IconMail, IconPhone } from '@tabler/icons-react'

import DzenIcon from '@/assets/icons/social/dzen'
import { widgetLinkClass } from '@/components/ui/widget'

import { useSite } from '@/lib/site'
import { formatPhone } from '@/lib/format'

// Cartzilla's light outlined social buttons, white with the brand color on hover
const socialClass = 'inline-flex size-9 items-center justify-center rounded-md border border-white/12 text-white transition-colors hover:border-transparent hover:bg-white'
const captionClass = 'mb-2 text-xs text-white opacity-50'
const linkIcon = { size: 16, stroke: 1.5, className: 'me-1 -mt-0.5 align-middle' }

export default function BottomBar() {
  const { site } = useSite()

  return (
    // below lg the handheld toolbar covers the bottom of the page
    <footer className="shrink-0 bg-dark pt-12 pb-14 lg:pb-0">
      <div className="container">
        <div className="grid gap-x-7.5 pb-2 md:grid-cols-2">
          <div className="mb-6 text-center md:text-start">
            <ul className="flex flex-wrap justify-center md:justify-start">
              <li className="me-6 mb-2">
                <Link className={widgetLinkClass({ light: true })} href="/pages/articles/">
                  Справочные материалы
                </Link>
              </li>
              <li className="me-6 mb-2">
                <Link className={widgetLinkClass({ light: true })} href="/blog/entries">
                  Блог
                </Link>
              </li>
            </ul>
          </div>
          <div className="mb-6 text-center md:text-end">
            <div className="mb-2">
              <a className={widgetLinkClass({ light: true })} href="mailto:info@thsm.ru">
                <IconMail {...linkIcon} />
                info@thsm.ru
              </a>
            </div>
            <div className="block gap-4 md:flex md:justify-end">
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
              <div>
                <div className={captionClass}>Розничные магазины:</div>
                <div className="mb-2">
                  <a className={widgetLinkClass({ light: true })} href={"tel:" + "+74957440087"}>
                    <IconPhone {...linkIcon} />
                    {formatPhone("+74957440087")}
                  </a>
                </div>
              </div>
            </div>
            <div className={captionClass}>Наши страницы в соцсетях:</div>
            <div className="mb-2 flex justify-center gap-2 md:justify-end">
              <a className={`${socialClass} hover:text-[#45668e]`} href="https://vk.com/sew.world" aria-label="ВКонтакте">
                <IconBrandVk size={20} stroke={1.5} />
              </a>
              <a className={`${socialClass} p-[.35rem] hover:text-[#353535]`} href="https://shorturl.at/ZzJbf" aria-label="Дзен">
                <DzenIcon className="size-full" />
              </a>
              <a className={`${socialClass} hover:text-[#08c]`} href="https://t.me/sewingworldrus" aria-label="Telegram">
                <IconBrandTelegram size={20} stroke={1.5} />
              </a>
              <a className={`${socialClass} hover:text-[red]`} href="https://youtube.com/%D0%A8%D0%B2%D0%B5%D0%B9%D0%BD%D1%8B%D0%B9%D0%9C%D0%B8%D1%80%D0%A0%D0%BE%D1%81%D1%81%D0%B8%D1%8F" aria-label="YouTube">
                <IconBrandYoutubeFilled size={20} />
              </a>
            </div>
            <div className="mb-4 text-xs text-white opacity-50">Присоединяйтесь!</div>
          </div>
        </div>
        <div className="pb-6 text-center text-xs text-white opacity-50 md:text-start">
          &copy; 2003-{new Date().getFullYear()} Швейный Мир. Все права защищены.{' '}
          <span className="opacity-50">
            Developed by <a className="text-white" href="https://newf.ru/" target="_blank" rel="noopener">Andrey Novikov</a>.
            Design by <a className="text-white" href="https://createx.studio/" target="_blank" rel="noopener">Createx Studio</a>.
          </span>
        </div>
      </div>
    </footer>
  )
}
