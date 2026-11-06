'use client'

import { ReactNode } from 'react'

import { Collapsible } from '@base-ui/react/collapsible'

// The menu collapses below lg. The panel stays mounted, so its links are in the static HTML,
// and .navbar-expand-lg shows it from lg up.
export default function Navbar({ brand, children }: { brand: ReactNode, children: ReactNode }) {
  return (
    <Collapsible.Root className="container-fluid">
      {brand}
      <Collapsible.Trigger className="navbar-toggler" aria-label="Меню">
        <span className="navbar-toggler-icon"></span>
      </Collapsible.Trigger>
      <Collapsible.Panel className="navbar-collapse sw-collapse-lg-down" id="navbarNav" keepMounted>
        {children}
      </Collapsible.Panel>
    </Collapsible.Root>
  )
}
