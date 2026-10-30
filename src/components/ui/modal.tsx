'use client'

import { ReactNode } from 'react'

import { Dialog } from '@base-ui/react/dialog'

import { shown } from './transition'

// Base UI dialog rendered with Bootstrap .modal markup, the popup is .modal-content so clicks around it count as outside presses.
// With `staticBackdrop` it isn't closed by clicking outside, only by Escape or explicitly.
export function Modal({
  show,
  onHide,
  staticBackdrop = false,
  children
}: {
  show: boolean,
  onHide: () => void,
  staticBackdrop?: boolean,
  children: ReactNode
}) {
  return (
    <Dialog.Root open={show} onOpenChange={(open) => !open && onHide()} disablePointerDismissal={staticBackdrop}>
      <Dialog.Portal>
        <Dialog.Backdrop className={(state) => 'modal-backdrop fade' + (shown(state) ? ' show' : '')} />
        <Dialog.Viewport className={(state) => 'modal fade d-block' + (shown(state) ? ' show' : '')}>
          <div className="modal-dialog modal-dialog-centered">
            <Dialog.Popup className="modal-content">
              {children}
            </Dialog.Popup>
          </div>
        </Dialog.Viewport>
      </Dialog.Portal>
    </Dialog.Root>
  )
}

export function ModalHeader({ className = '', children }: { className?: string, children: ReactNode }) {
  return (
    <div className={`modal-header ${className}`}>
      {children}
      <Dialog.Close className="btn-close" aria-label="Закрыть" />
    </div>
  )
}

export function ModalBody({ className = '', children }: { className?: string, children: ReactNode }) {
  return (
    <div className={`modal-body ${className}`}>
      {children}
    </div>
  )
}

export function ModalFooter({ className = '', children }: { className?: string, children: ReactNode }) {
  return (
    <div className={`modal-footer ${className}`}>
      {children}
    </div>
  )
}
