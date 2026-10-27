'use client'

import { createContext, useContext, CSSProperties, ReactNode } from 'react'

import { Dialog } from '@base-ui/react/dialog'

import { useBreakpoint } from '@/lib/breakpoint'

import { shown } from './transition'

const OffcanvasContext = createContext<() => void>(() => {})

// Sidebar that is rendered inline from lg up (see .offcanvas-lg in styles.scss) and slides in as a Base UI dialog below lg.
// While it isn't open it is rendered inline below lg too and .offcanvas keeps it off screen, so its content is always in the page.
export default function Offcanvas({
  show,
  onHide,
  className = '',
  style,
  children
}: {
  show: boolean,
  onHide: () => void,
  className?: string,
  style?: CSSProperties,
  children: ReactNode
}) {
  const breakpoint = useBreakpoint()
  const open = show && !['lg', 'xl', 'xxl'].includes(breakpoint)
  const classes = `offcanvas ${className} offcanvas-lg offcanvas-start`

  return (
    <OffcanvasContext.Provider value={onHide}>
      {!open && (
        <div className={classes} style={style}>
          {children}
        </div>
      )}
      <Dialog.Root open={open} onOpenChange={(open) => !open && onHide()}>
        <Dialog.Portal>
          <Dialog.Backdrop className={(state) => 'modal-backdrop fade' + (shown(state) ? ' show' : '')} />
          <Dialog.Popup className={(state) => classes + (shown(state) ? ' show' : '')} style={style}>
            {children}
          </Dialog.Popup>
        </Dialog.Portal>
      </Dialog.Root>
    </OffcanvasContext.Provider>
  )
}

export function OffcanvasHeader({ className = '', children }: { className?: string, children: ReactNode }) {
  const onHide = useContext(OffcanvasContext)

  return (
    <div className={`offcanvas-header ${className}`}>
      {children}
      <button type="button" className="btn-close" aria-label="Закрыть" onClick={onHide} />
    </div>
  )
}

export function OffcanvasBody({ className = '', children }: { className?: string, children: ReactNode }) {
  return (
    <div className={`offcanvas-body ${className}`}>
      {children}
    </div>
  )
}
