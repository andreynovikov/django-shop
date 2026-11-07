'use client'

import { useState, useEffect } from 'react'
import { IconChevronUp } from '@tabler/icons-react'

export default function ScrollTopButton() {
  const [show, setShow] = useState(false)

  useEffect(() => {
    const setVisibleState = () => {
      setShow(window.scrollY > 600)
    }
    window.addEventListener('scroll', setVisibleState)
    return () => {
      window.removeEventListener('scroll', setVisibleState)
    }
  }, [])

  const handleScroll = () => {
    window.scrollTo({
      top: 0,
      left: 0,
      behavior: 'smooth'
    })
  }

  // slides in from the right with a bounce, sits above the handheld toolbar below lg
  return (
    <button
      className={`group fixed bottom-[4.5rem] z-1025 flex size-[2.2rem] items-center justify-center rounded-full bg-gray-900/25 text-white transition-[right,opacity,background-color] duration-[400ms,300ms,250ms] ease-[cubic-bezier(.68,-.55,.265,1.55),ease,ease-in-out] hover:bg-gray-900/50 min-[500px]:size-11 lg:bottom-5 ${show ? 'right-4 opacity-100 min-[500px]:right-5' : '-right-[4.125rem] opacity-0'}`}
      onClick={handleScroll}
      aria-label="Начало страницы">
      <span className="invisible absolute top-1/2 right-full me-2 -translate-y-1/2 text-sm text-muted opacity-0 transition-[opacity,visibility] duration-250 group-hover:visible group-hover:opacity-100">Начало</span>
      <IconChevronUp size={16} stroke={2.5} />
    </button>
  )
}
