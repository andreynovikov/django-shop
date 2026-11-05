'use client'

import { useEffect, useRef, useState, useSyncExternalStore } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

import { Collapsible } from '@base-ui/react/collapsible'

import { IconMenu2 } from '@tabler/icons-react'

import CompareLink from '@/components/user/compare-link'

import useComparison from '@/lib/comparison'

const subscribeToScroll = (callback: () => void) => {
  window.addEventListener('scroll', callback, { passive: true })
  return () => window.removeEventListener('scroll', callback)
}

export default function Header() {
  const pathname = usePathname()
  // the menu is open on the page where it was opened, so it closes on navigation
  const [menuOpenAt, setMenuOpenAt] = useState<string | null>(null)
  const navRef = useRef<HTMLElement>(null)

  const { comparisons } = useComparison()

  // the home page has a transparent header over its banners
  const transparent = pathname === '/'
  // the navbar is affixed as soon as the page is scrolled
  const fixed = useSyncExternalStore(subscribeToScroll, () => window.scrollY > 0, () => false)

  useEffect(() => {
    // keep the content in place when the navbar leaves the flow, the transparent header is out of it anyway
    document.body.style.paddingTop = fixed && !transparent && navRef.current ? `${navRef.current.offsetHeight}px` : ''
  }, [fixed, transparent])

  return (
    <header className={"header" + (transparent ? " header-absolute" : "")}>
      <nav
        ref={navRef}
        className={
          "navbar navbar-expand-lg navbar-sticky navbar-airy navbar-light " +
          (transparent ? "bg-transparent bg-hover-white bg-fixed-white navbar-hover-light navbar-fixed-light" : "bg-white bg-fixed-white") +
          (fixed ? " fixed-top" : "")
        }>
        <Collapsible.Root
          className="container-fluid"
          open={menuOpenAt === pathname}
          onOpenChange={(open) => setMenuOpenAt(open ? pathname : null)}>
          <Link className="navbar-brand" href="/">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/i/logo.svg" alt="Швейная техника и аксессуары Family" className="img-responsive" />
          </Link>
          <Collapsible.Trigger className="navbar-toggler navbar-toggler-right" aria-label="Toggle navigation">
            <IconMenu2 />
          </Collapsible.Trigger>
          {/* Kept in the DOM for crawlers, the expanded navbar shows it from lg up */}
          <Collapsible.Panel className="navbar-collapse sw-collapse-lg-down mt-2 mt-sm-0" keepMounted>
            <ul className="navbar-nav mx-auto">
              <li className="nav-item">
                <Link className="nav-link" href="/catalog/sewing_machines/">Швейные машины</Link>
              </li>
              <li className="nav-item">
                <Link className="nav-link" href="/catalog/overlock/">Оверлоки</Link>
              </li>
              <li className="nav-item">
                <Link className="nav-link" href="/catalog/accessories/">Аксессуары</Link>
              </li>
              <li className="nav-item">
                <Link className="nav-link" href="/news/">Новости</Link>
              </li>
              <li className="nav-item">
                <Link className="nav-link" href="/pages/about/">История</Link>
              </li>
              <li className="nav-item">
                <Link className="nav-link" href="/stores/">Где купить</Link>
              </li>
              <li className="nav-item">
                <Link className="nav-link" href="/service/">Поддержка</Link>
              </li>
            </ul>
            <div className="d-flex align-items-center justify-content-between justify-content-lg-end mt-1 mb-2 my-lg-0">
              {comparisons.length > 0 && (
                <div className="nav-item">
                  <Link href="/compare/" className="navbar-icon-link">
                    <CompareLink />
                  </Link>
                </div>
              )}
            </div>
          </Collapsible.Panel>
        </Collapsible.Root>
      </nav>
    </header>
  )
}
