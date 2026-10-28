'use client'

import { ReactNode, useEffect, useRef } from 'react'

function updateSidebarStyle(container: HTMLElement, sidebar: HTMLElement, scrollOffset: number) {
  const navbar = document.querySelector<HTMLElement>('.sw-navbar')
  if (navbar === null || sidebar.parentElement === null)
    return

  const containerRect = container.getBoundingClientRect()
  const sidebarRect = sidebar.getBoundingClientRect()
  const parentWidth = sidebar.parentElement.offsetWidth

  const state = sidebar.dataset.state
  const availableHeight = window.innerHeight - 20
  const isSidebarTopVisible = sidebarRect.top > navbar.offsetHeight
  const isSidebarTaller = sidebarRect.height > availableHeight - navbar.offsetHeight

  if ([undefined, 'relativeBottom'].includes(state) && scrollOffset > 0 && containerRect.top < navbar.offsetHeight && sidebarRect.bottom < availableHeight && isSidebarTaller) {
    sidebar.style.setProperty('position', 'fixed')
    sidebar.style.setProperty('top', 'auto', 'important')
    sidebar.style.setProperty('bottom', '20px', 'important')
    sidebar.style.setProperty('width', parentWidth + 'px', 'important')
    sidebar.dataset.state = 'fixedBottom'
  }
  if (['fixedTop', 'fixedBottom'].includes(state!) && containerRect.bottom < availableHeight && scrollOffset > 0) {
    sidebar.style.setProperty('position', 'absolute')
    sidebar.style.setProperty('top', 'auto', 'important')
    sidebar.style.setProperty('bottom', '20px', 'important')
    sidebar.style.setProperty('width', parentWidth + 'px', 'important')
    sidebar.dataset.state = 'absoluteBottom'
  }
  if (
    (['absoluteBottom'].includes(state!) && sidebarRect.bottom > window.innerHeight) ||
    (['fixedBottom', 'absoluteBottom'].includes(state!) && scrollOffset < 0) ||
    (['fixedTop'].includes(state!) && scrollOffset > 0 && isSidebarTaller)
  ) {
    sidebar.style.setProperty('position', 'relative')
    sidebar.style.setProperty('top', (sidebarRect.top - containerRect.top) + 'px', 'important')
    sidebar.style.setProperty('bottom', 'auto', 'important')
    sidebar.style.removeProperty('width')
    sidebar.dataset.state = 'relativeBottom'
  }
  if (
    (['relativeBottom', 'absoluteBottom'].includes(state!) && scrollOffset < 0 && isSidebarTopVisible && !isSidebarTaller) ||
    (['relativeBottom', 'fixedBottom', 'absoluteBottom'].includes(state!) && scrollOffset < 0 && isSidebarTopVisible && containerRect.bottom > window.innerHeight && sidebarRect.bottom > window.innerHeight) ||
    (state === undefined && scrollOffset > 0 && !isSidebarTopVisible && !isSidebarTaller)
  ) {
    sidebar.style.setProperty('position', 'fixed')
    sidebar.style.setProperty('top', navbar.offsetHeight + 'px', 'important')
    sidebar.style.setProperty('bottom', 'auto', 'important')
    sidebar.style.setProperty('width', parentWidth + 'px', 'important')
    sidebar.dataset.state = 'fixedTop'
  }
  if (['fixedTop', 'fixedBottom'].includes(state!) && containerRect.top > navbar.offsetHeight) {
    sidebar.style.setProperty('position', 'relative')
    sidebar.style.setProperty('top', 'auto', 'important')
    sidebar.style.setProperty('bottom', 'auto', 'important')
    sidebar.style.removeProperty('width')
    delete sidebar.dataset.state
  }
}

// Sidebar column that sticks to the navbar while scrolling and to the page bottom when it is taller than the window
export default function StickySidebar({ className, children }: { className?: string, children: ReactNode }) {
  const containerRef = useRef<HTMLElement>(null)
  const sidebarRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    let pageYOffset = window.scrollY

    const updateSidebarWidth = () => {
      const sidebar = sidebarRef.current
      if (sidebar === null || sidebar.parentElement === null)
        return

      if (['fixedTop', 'fixedBottom', 'absoluteBottom'].includes(sidebar.dataset.state!))
        sidebar.style.setProperty('width', sidebar.parentElement.offsetWidth + 'px', 'important')
    }

    const updateSidebarPosition = () => {
      if (containerRef.current !== null && sidebarRef.current !== null)
        updateSidebarStyle(containerRef.current, sidebarRef.current, window.scrollY - pageYOffset)
      pageYOffset = window.scrollY
    }

    window.addEventListener('resize', updateSidebarWidth)
    window.addEventListener('scroll', updateSidebarPosition)

    return () => {
      window.removeEventListener('resize', updateSidebarWidth)
      window.removeEventListener('scroll', updateSidebarPosition)
    }
  }, [])

  return (
    <aside className={`position-relative ${className ?? ''}`} ref={containerRef}>
      <div style={{ maxWidth: "22rem" }}>
        <div ref={sidebarRef}>
          {children}
        </div>
      </div>
    </aside>
  )
}
