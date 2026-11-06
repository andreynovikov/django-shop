'use client'

import { ReactNode } from 'react'

import { Collapsible } from '@base-ui/react/collapsible'

import { IconMenu2 } from '@tabler/icons-react'

import { navbarContentClass } from '@/components/ui/navbar'

// The menu collapses below lg. The panel stays mounted, so its links are in the static HTML,
// and from lg up it is always shown, see .sw-shown-lg in styles.css. Its height is animated below lg.
export default function Navbar({ brand, children }: { brand: ReactNode, children: ReactNode }) {
  return (
    <Collapsible.Root className={navbarContentClass}>
      {brand}
      <Collapsible.Trigger
        className="rounded-md border border-black/15 px-3 py-1 text-lg leading-none text-black/65 transition-shadow focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-black/25 lg:hidden"
        aria-label="Меню">
        <IconMenu2 className="size-[1.5em] text-muted" stroke={1.5} />
      </Collapsible.Trigger>
      <Collapsible.Panel
        className="sw-shown-lg grow basis-full lg:basis-auto max-lg:h-(--collapsible-panel-height) max-lg:overflow-hidden max-lg:transition-[height] max-lg:duration-350 max-lg:data-ending-style:h-0 max-lg:data-starting-style:h-0"
        id="navbarNav"
        keepMounted>
        <div className="items-center lg:flex">
          {children}
        </div>
      </Collapsible.Panel>
    </Collapsible.Root>
  )
}
