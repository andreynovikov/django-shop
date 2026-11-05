'use client'

import { useEffect, useRef, useState, useSyncExternalStore } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

import { Collapsible } from '@base-ui/react/collapsible'

import { IconMenu2 } from '@tabler/icons-react'

import CompareLink from '@/components/user/compare-link'

import useComparison from '@/lib/comparison'

// The product rating link scrolls the page below the navbar
export const navbarId = 'navbar'

const links = [
  { href: '/catalog/sewing_machines/', label: 'Швейные машины' },
  { href: '/catalog/overlock/', label: 'Оверлоки' },
  { href: '/catalog/accessories/', label: 'Аксессуары' },
  { href: '/news/', label: 'Новости' },
  { href: '/pages/about/', label: 'История' },
  { href: '/stores/', label: 'Где купить' },
  { href: '/service/', label: 'Поддержка' },
]

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
    <header className={"select-none" + (transparent ? " absolute inset-x-0 top-0 z-1030" : "")}>
      <nav
        ref={navRef}
        id={navbarId}
        data-fixed={fixed || undefined}
        className={
          "px-4 py-2.5 transition-[background-color] duration-200 lg:py-4 " +
          (transparent && !fixed ? "bg-transparent hover:bg-white" : "bg-white") +
          (fixed ? " fixed inset-x-0 top-0 z-1030 shadow-lg" : "")
        }>
        <Collapsible.Root
          className="flex flex-wrap items-center justify-between px-3 lg:flex-nowrap lg:justify-start"
          open={menuOpenAt === pathname}
          onOpenChange={(open) => setMenuOpenAt(open ? pathname : null)}>
          <Link className="me-4 py-1" href="/">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/i/logo.svg" alt="Швейная техника и аксессуары Family" className="max-w-60 sm:max-w-75" />
          </Link>
          <Collapsible.Trigger className="border border-transparent px-3 py-1 text-black/65 lg:hidden" aria-label="Toggle navigation">
            <IconMenu2 />
          </Collapsible.Trigger>
          {/* Kept in the DOM for crawlers. Below lg its height is animated, from lg up it is always shown, see .sw-shown-lg in styles.css */}
          <Collapsible.Panel
            className="sw-shown-lg mt-2 basis-full sm:mt-0 lg:grow lg:basis-auto max-lg:h-(--collapsible-panel-height) max-lg:max-h-[80vh] max-lg:overflow-y-auto max-lg:transition-[height] max-lg:duration-350 max-lg:data-ending-style:h-0 max-lg:data-starting-style:h-0"
            keepMounted>
            <div className="lg:flex lg:items-center">
              <ul className="flex flex-col lg:mx-auto lg:flex-row">
                {links.map(({ href, label }) => (
                  <li key={href}>
                    <Link
                      className="block py-2 text-[.9rem] font-bold tracking-[.15em] text-black/65 uppercase transition-colors hover:text-black/95 hover:no-underline lg:px-3 xl:px-5"
                      href={href}>
                      {label}
                    </Link>
                  </li>
                ))}
              </ul>
              <div className="mt-1 mb-2 flex items-center justify-between lg:my-0 lg:justify-end">
                {comparisons.length > 0 && (
                  <div className="relative">
                    <Link href="/compare/" className="mx-2 flex items-center py-1.5 text-black/95 hover:no-underline">
                      <CompareLink />
                    </Link>
                  </div>
                )}
              </div>
            </div>
          </Collapsible.Panel>
        </Collapsible.Root>
      </nav>
    </header>
  )
}
