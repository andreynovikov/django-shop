'use client'

import { AnchorHTMLAttributes, MouseEvent } from 'react'

// In-page anchor that scrolls smoothly, Cartzilla disables CSS smooth scrolling
export function ScrollLink({ href, children, ...props }: AnchorHTMLAttributes<HTMLAnchorElement> & { href: `#${string}` }) {
  const handleClick = (event: MouseEvent<HTMLAnchorElement>) => {
    const el = document.getElementById(href.substring(1))
    if (el === null)
      return

    event.preventDefault()
    el.scrollIntoView({
      behavior: 'smooth',
      block: 'start'
    })
  }

  return (
    <a href={href} onClick={handleClick} {...props}>
      {children}
    </a>
  )
}
