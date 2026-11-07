import { ComponentProps } from 'react'

import { IconX } from '@tabler/icons-react'

// Bootstrap's .btn-close: a faded cross that darkens on hover. Base UI parts can render it, e.g. `<Dialog.Close render={<CloseButton />} />`.
export default function CloseButton({ className = '', ...props }: ComponentProps<'button'>) {
  return (
    <button type="button" aria-label="Закрыть" className={`p-1 text-black opacity-50 transition-opacity hover:opacity-75 ${className}`} {...props}>
      <IconX size={16} stroke={2} className="block" />
    </button>
  )
}
