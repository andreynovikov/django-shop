'use client'

import { useState, useEffect, useRef, ReactNode } from 'react'
import Link from 'next/link'

import { IconCategory, IconHeadset, IconHeart, IconMapPin, IconMenu2, IconX } from '@tabler/icons-react'

import { Collapsible } from '@base-ui/react/collapsible'
import { Menu } from '@base-ui/react/menu'

import CartNotice from '@/components/cart/notice'
import OrderTracking from '@/components/order/tracking'
import CompareLink from '@/components/user/compare-link'
import UserProfileLink from '@/components/user/profile-link'
import ProductSearchInput from '@/components/product/search-input'
import Tooltip from '@/components/ui/tooltip'
import { buttonClass } from '@/components/ui/button'
import { caretClass, navbarToolClass, navbarToolIconClass, navbarToolLabelClass } from '@/components/ui/navbar'

import CatalogDropDown from './catalog-dropdown'

import useComparison from '@/lib/comparison'
import useFavorites from '@/lib/favorites'
import { useSite } from '@/lib/site'
import { useSession } from '@/lib/session'
import { useTopbar } from '@/lib/topbar'
import { formatPhone } from '@/lib/format'

// The topbar's texts and links, their icons are primary
const topbarTextClass = 'inline-block whitespace-nowrap text-gray-700/90'
const topbarLinkClass = 'text-gray-700/90 hover:text-heading'
const topbarIcon = { size: '1.15em', stroke: 1.5, className: '-mt-1 me-1.5 align-middle text-primary' }

// A link of the main menu: in gray boxes below md, in a row from md up
const navItemClass = 'mb-[.667rem] rounded-md bg-gray-100 md:mb-0 md:bg-transparent'
const navLinkClass = 'block px-[1.125rem] py-[.667rem] font-medium text-gray-700 transition-colors hover:text-primary md:pt-[1.125rem] md:pb-[.875rem] md:font-normal'

// catalog is rendered by the caller, so App Router renders it on the server
export default function TopBar({ catalog }: { catalog: ReactNode }) {
  const [catalogVisible, setCatalogVisible] = useState(false)
  // from lg up, once the page is scrolled below the header, the header sticks to the top without its menu row,
  // the stuck menu toggler shows the menu row again
  const [stuck, setStuck] = useState(false)
  const [stuckMenuOpen, setStuckMenuOpen] = useState(false)
  const { site } = useSite()
  const { status } = useSession()
  const { hideSignIn, hideCartNotice, topMenuOpen, toggleTopMenu } = useTopbar()

  const navbarRef = useRef<HTMLDivElement>(null)
  const stickyRef = useRef<HTMLDivElement>(null)
  const stuckRef = useRef(false)
  const catalogButtonRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    const setStuckState = (value: boolean) => {
      if (stuckRef.current === value)
        return
      stuckRef.current = value
      setStuck(value)
      if (value)
        setStuckMenuOpen(false)
    }

    if (catalogVisible && window.innerWidth >= 1024 /* lg */ && stuckRef.current)
      window.scrollTo(0, 0)

    const setNavbarState = () => {
      const headerHeight = (navbarRef.current?.offsetHeight ?? 0) - 15
      const offset = (stickyRef.current?.getBoundingClientRect().bottom ?? 0) + window.scrollY
      if (offset >= headerHeight && !catalogVisible)
        setStuckState(true)
      else if (offset < headerHeight)
        setStuckState(false)
    }

    window.addEventListener('scroll', setNavbarState)

    return () => {
      window.removeEventListener('scroll', setNavbarState)
    }
  }, [catalogVisible])

  const { comparisons } = useComparison()
  const { favorites } = useFavorites()

  const seoLogoAlt = "Janome.Club - Фирменный магазин Janome. Швейные машины, вышивальные машины, оверлоки и аксессуары."

  // sticky classes apply from lg up only
  const sticky = 'lg:sticky lg:top-0 lg:z-1030'

  return (
    <header id="navbar" className={stuck ? `${sticky} lg:pointer-events-none` : ''} ref={navbarRef}>
      <div
        className={`bg-white ${catalogVisible ? '' : sticky} ${stuck ? `lg:pointer-events-auto ${stuckMenuOpen ? '' : 'lg:shadow-md'}` : ''}`}
        ref={stickyRef}>
        <div className="bg-topbar py-2.5 text-sm">
          <div className="container flex items-center justify-between">
            <div className="flex grow justify-between md:block">
              <Menu.Root>
                <Menu.Trigger className={`${topbarTextClass} cursor-pointer lg:hidden ${caretClass}`} nativeButton={false} render={<div />}>
                  <IconHeadset {...topbarIcon} />
                  Телефоны
                </Menu.Trigger>
                <Menu.Portal>
                  <Menu.Positioner sideOffset={8} className="z-1000">
                    <Menu.Popup className="flex flex-col items-start gap-2 rounded-md border border-gray-300 bg-white p-4 text-sm shadow-md">
                      <div className={topbarTextClass}>
                        <a className={topbarLinkClass} href={"tel:" + "+74957844855"}>{formatPhone("+74957844855")}</a>
                        <span className="text-muted">&nbsp;&ndash;&nbsp;Магазин на Автозаводской</span>
                      </div>
                      {site.phone && (
                        <div className={topbarTextClass}>
                          <a className={topbarLinkClass} href={"tel:" + site.phone}>{formatPhone(site.phone)}</a>
                          <span className="text-muted">&nbsp;&ndash;&nbsp;Интернет-магазин</span>
                        </div>
                      )}
                    </Menu.Popup>
                  </Menu.Positioner>
                </Menu.Portal>
              </Menu.Root>
              <div className={`hidden whitespace-nowrap text-gray-700/90 lg:inline-block ${site.phone ? 'me-4 border-e pe-4' : ''}`}>
                <IconHeadset {...topbarIcon} />
                <a className={topbarLinkClass} href={"tel:" + "+74957844855"}>{formatPhone("+74957844855")}</a>
                <span className="text-muted/90">&nbsp;&ndash;&nbsp;Магазин на Автозаводской</span>
              </div>
              {site.phone && (
                <div className="hidden whitespace-nowrap text-gray-700/90 lg:inline-block">
                  <IconHeadset {...topbarIcon} />
                  <a className={topbarLinkClass} href={"tel:" + site.phone}>{formatPhone(site.phone)}</a>
                  <span className="text-muted/90">&nbsp;&ndash;&nbsp;Интернет-магазин</span>
                </div>
              )}
              <div className={`hidden w-0 md:inline-block lg:hidden ${site.phone ? 'ms-4 border-s ps-4' : ''}`}>&nbsp;</div>
              <div className={`${topbarTextClass} lg:hidden`}>
                <IconMapPin {...topbarIcon} />
                <Link className={topbarLinkClass} href="/stores/">
                  Магазины
                </Link>
              </div>
            </div>
            <div className="hidden md:block">
              {comparisons.length > 0 && (
                <Link className={`${topbarLinkClass} whitespace-nowrap`} href="/compare" rel="nofollow">
                  <CompareLink />
                </Link>
              )}
              <OrderTracking addDivider={comparisons.length > 0} />
            </div>
          </div>
        </div>
        <div className="relative py-3">
          <div className="container flex flex-wrap items-center justify-between lg:flex-nowrap lg:justify-start">
            <Link className="me-4 inline-block shrink-0 py-2.5 align-middle" href="/">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src="/i/logo.svg" alt={seoLogoAlt} className="h-[35px] w-auto object-cover object-left xl:h-[44px]" />
            </Link>
            <div className="mx-2 hidden grow md:flex lg:mx-6 lg:w-full">
              <ProductSearchInput />
            </div>
            <div className="flex shrink-0 items-center">
              <button className="p-3 leading-none text-gray-700 md:hidden" type="button" onClick={toggleTopMenu} aria-label="Разделы сайта">
                <IconMenu2 size="1.5em" stroke={1.5} className="align-middle" />
              </button>
              <Tooltip content="Раскрыть меню">
                <button
                  className={`${navbarToolClass} ${stuck ? 'hidden lg:flex' : 'hidden'}`}
                  onClick={() => setStuckMenuOpen(!stuckMenuOpen)}
                  aria-label="Раскрыть меню">
                  <div className={navbarToolIconClass()}><IconMenu2 size={22} stroke={1.5} /></div>
                </button>
              </Tooltip>
              {status === 'authenticated' && (
                <Tooltip content="Избранное">
                  <Link className={`${navbarToolClass} hidden lg:flex`} href="/user/favorites" aria-label="Избранное">
                    <div className={navbarToolIconClass()}>
                      {favorites.length > 0 && <span className={navbarToolLabelClass}>{favorites.length}</span>}
                      <IconHeart size={22} stroke={1.5} />
                    </div>
                  </Link>
                </Tooltip>
              )}
              {!hideSignIn && <UserProfileLink />}
              {!hideCartNotice && <CartNotice />}
            </div>
          </div>
        </div>
      </div>
      <nav className={`relative bg-white pt-0 pb-2 ${stuck ? (stuckMenuOpen ? 'lg:pointer-events-auto lg:shadow-md' : 'lg:invisible') : ''}`} aria-label="Разделы сайта">
        <Collapsible.Root className="container flex flex-wrap items-center justify-between md:flex-nowrap md:justify-start" open={topMenuOpen}>
          <div className="flex gap-2">
            <ul className="my-4 flex flex-col lg:my-0 lg:me-2 lg:pe-2">
              <li>
                <button ref={catalogButtonRef}
                  className={`${buttonClass({ variant: 'secondary', block: true, start: true })} text-lg! lg:justify-center ${caretClass}`}
                  onClick={() => setCatalogVisible(!catalogVisible)}>
                  <span className="me-2 hidden md:inline">
                    {catalogVisible ? <IconX stroke={1.5} className="block" /> : <IconCategory stroke={1.5} className="block" />}
                  </span>
                  Каталог
                </button>
                <CatalogDropDown catalog={catalog} visible={catalogVisible} setVisible={setCatalogVisible} buttonRef={catalogButtonRef} />
              </li>
            </ul>
            {!catalogVisible && <div className="my-4 shrink md:hidden">
              <ProductSearchInput mobile />
            </div>}
          </div>
          <Collapsible.Panel
            className="sw-shown-md grow basis-full md:basis-auto max-md:h-(--collapsible-panel-height) max-md:overflow-hidden max-md:transition-[height] max-md:duration-350 max-md:data-ending-style:h-0 max-md:data-starting-style:h-0"
            keepMounted>
            <ul className="flex flex-col md:flex-row">
              <li className={navItemClass}>
                <Link className={navLinkClass} href="/stores/">
                  Магазины
                </Link>
              </li>
              <li className={navItemClass}>
                <Link className={navLinkClass} href="/pages/delivery/">
                  Доставка
                </Link>
              </li>
              <li className={`${navItemClass} md:hidden`}>
                <Link className={navLinkClass} href="/user/orders?track" rel="nofollow">
                  Состояние заказа
                </Link>
              </li>
            </ul>
          </Collapsible.Panel>
        </Collapsible.Root>
      </nav>
    </header>
  )
}
