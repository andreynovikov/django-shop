'use client'

import { ReactNode } from 'react'

import { Dialog } from '@base-ui/react/dialog'

import CloseButton from './close-button'

// Base UI dialog in the middle of the screen. The popup is only the white box, so clicks around it count as outside presses.
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
        <Dialog.Backdrop className="fixed inset-0 z-1040 bg-black opacity-50 transition-opacity duration-150 data-ending-style:opacity-0 data-starting-style:opacity-0" />
        <Dialog.Viewport className="fixed inset-0 z-1060 overflow-y-auto">
          <div className="pointer-events-none m-2 flex min-h-[calc(100%-1rem)] items-center sm:mx-auto sm:my-7 sm:min-h-[calc(100%-3.5rem)] sm:max-w-[500px]">
            <Dialog.Popup className="pointer-events-auto relative flex w-full flex-col rounded-lg border border-gray-300 bg-white shadow-lg transition-[opacity,translate] duration-300 ease-out data-ending-style:-translate-y-12 data-ending-style:opacity-0 data-starting-style:-translate-y-12 data-starting-style:opacity-0">
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
    <div className={`flex shrink-0 items-center justify-between rounded-t-lg border-b border-gray-300 px-5 py-4 ${className}`}>
      {children}
      <Dialog.Close render={<CloseButton />} />
    </div>
  )
}

export function ModalBody({ className = '', children }: { className?: string, children: ReactNode }) {
  return (
    <div className={`relative flex-auto p-5 ${className}`}>
      {children}
    </div>
  )
}

export function ModalFooter({ className = '', children }: { className?: string, children: ReactNode }) {
  return (
    <div className={`flex shrink-0 flex-wrap items-center justify-end gap-2 rounded-b-lg border-t border-gray-300 p-4 ${className}`}>
      {children}
    </div>
  )
}
