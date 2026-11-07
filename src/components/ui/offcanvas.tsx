'use client'

import { createContext, useContext, ReactNode } from 'react'

import { Dialog } from '@base-ui/react/dialog'

import { useBreakpoint } from '@/lib/breakpoint'

import CloseButton from './close-button'

const OffcanvasContext = createContext<() => void>(() => {})

// A white sidebar panel that is inline from lg up and slides in from the left as a Base UI dialog below lg
const panelClass = 'fixed inset-y-0 left-0 z-1080 flex w-full max-w-[22rem] flex-col bg-white py-1 lg:static lg:z-auto lg:translate-x-0 lg:rounded-lg lg:shadow-lg'

// Sidebar that is rendered inline from lg up and slides in as a Base UI dialog below lg.
// While it isn't open it is rendered inline below lg too, off screen, so its content is always in the page.
export default function Offcanvas({
  show,
  onHide,
  children
}: {
  show: boolean,
  onHide: () => void,
  children: ReactNode
}) {
  const breakpoint = useBreakpoint()
  const open = show && !['lg', 'xl', 'xxl'].includes(breakpoint)

  return (
    <OffcanvasContext.Provider value={onHide}>
      {!open && (
        <div className={`${panelClass} -translate-x-full`}>
          {children}
        </div>
      )}
      <Dialog.Root open={open} onOpenChange={(open) => !open && onHide()}>
        <Dialog.Portal>
          <Dialog.Backdrop className="fixed inset-0 z-1040 bg-black opacity-50 transition-opacity duration-150 data-ending-style:opacity-0 data-starting-style:opacity-0" />
          <Dialog.Popup className={`${panelClass} shadow-lg transition-transform duration-400 ease-[cubic-bezier(.165,.84,.44,1)] data-ending-style:-translate-x-full data-starting-style:-translate-x-full`}>
            {children}
          </Dialog.Popup>
        </Dialog.Portal>
      </Dialog.Root>
    </OffcanvasContext.Provider>
  )
}

export function OffcanvasHeader({ children }: { children: ReactNode }) {
  const onHide = useContext(OffcanvasContext)

  return (
    <div className="flex shrink-0 items-center justify-between px-6 py-5 shadow-sm lg:hidden">
      {children}
      <CloseButton onClick={onHide} />
    </div>
  )
}

export function OffcanvasBody({ children }: { children: ReactNode }) {
  return (
    <div className="grow overflow-y-auto px-6 py-7.5 lg:overflow-visible lg:px-7.5">
      {children}
    </div>
  )
}
