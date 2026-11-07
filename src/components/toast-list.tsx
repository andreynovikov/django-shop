'use client'

import { Toast } from '@base-ui/react/toast'
import { IconX } from '@tabler/icons-react'

// Base UI's stacked toasts: the front one is shown in full, those behind it peek out above it and shrink, hovering
// expands the stack. The positions come from Base UI's --toast-* variables.
const toastClass = [
  'absolute right-0 bottom-0 z-[calc(1040_-_var(--toast-index))] box-border h-(--height) w-full origin-bottom cursor-default',
  'rounded-sm bg-white bg-clip-padding p-4 text-gray-700 shadow-[0_2px_10px_rgb(0_0_0/0.1)] select-none',
  '[--gap:0.75rem] [--peek:0.75rem] [--scale:calc(max(0,1_-_(var(--toast-index)_*_0.1)))] [--shrink:calc(1_-_var(--scale))]',
  '[--height:var(--toast-frontmost-height,var(--toast-height))]',
  '[--offset-y:calc(var(--toast-offset-y)_*_-1_+_(var(--toast-index)_*_var(--gap)_*_-1)_+_var(--toast-swipe-movement-y))]',
  '[transition:transform_0.5s_cubic-bezier(0.22,1,0.36,1),opacity_0.5s,height_0.15s]',
  '[transform:translateX(var(--toast-swipe-movement-x))_translateY(calc(var(--toast-swipe-movement-y)_-_(var(--toast-index)_*_var(--peek))_-_(var(--shrink)_*_var(--height))))_scale(var(--scale))]',
  'data-expanded:h-(--toast-height) data-expanded:[transform:translateX(var(--toast-swipe-movement-x))_translateY(var(--offset-y))]',
  'data-starting-style:[transform:translateY(150%)] data-ending-style:[transform:translateY(150%)] data-ending-style:opacity-0 data-limited:opacity-0',
  'data-ending-style:data-[swipe-direction=up]:[transform:translateY(calc(var(--toast-swipe-movement-y)_-_150%))]',
  'data-ending-style:data-[swipe-direction=down]:[transform:translateY(calc(var(--toast-swipe-movement-y)_+_150%))]',
  'data-ending-style:data-[swipe-direction=left]:[transform:translateX(calc(var(--toast-swipe-movement-x)_-_150%))_translateY(var(--offset-y))]',
  'data-ending-style:data-[swipe-direction=right]:[transform:translateX(calc(var(--toast-swipe-movement-x)_+_150%))_translateY(var(--offset-y))]',
  // keeps the stack hovered while the pointer crosses the gap between toasts
  'after:absolute after:top-full after:left-0 after:h-[calc(var(--gap)_+_1px)] after:w-full after:content-[""]',
].join(' ')

export default function ToastList() {
  const { toasts } = Toast.useToastManager()

  return toasts.map(toast => (
    <Toast.Root key={toast.id} toast={toast} className={toastClass}>
      <Toast.Content className="overflow-hidden transition-opacity duration-250 data-behind:opacity-0 data-expanded:opacity-100">
        <Toast.Title className="m-0 text-[0.975rem] leading-5 font-medium" />
        <Toast.Description className="m-0 text-[0.925rem] leading-5" />
        <Toast.Close className="absolute top-2 right-2 flex size-5 items-center justify-center rounded-sm hover:bg-gray-100" aria-label="Закрыть">
          <IconX size={16} />
        </Toast.Close>
      </Toast.Content>
    </Toast.Root>
  ))
}
