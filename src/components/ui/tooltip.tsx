'use client'

import { ReactElement, ReactNode } from 'react'

import { Tooltip as BaseTooltip } from '@base-ui/react/tooltip'

type Side = BaseTooltip.Positioner.State['side']

// The arrow is a rotated square, Base UI places it along the popup edge facing the trigger and sets its data-side
const arrowClass = 'size-2 rotate-45 data-[side=bottom]:-top-1 data-[side=inline-end]:-left-1 data-[side=inline-start]:-right-1 data-[side=left]:-right-1 data-[side=right]:-left-1 data-[side=top]:-bottom-1'

// The popover's arrow has the popup border on its outer sides
const popoverArrowClass = 'size-2.5 rotate-45 border-gray-300 bg-white data-[side=bottom]:-top-[5px] data-[side=bottom]:border-s data-[side=bottom]:border-t data-[side=inline-end]:-left-[5px] data-[side=inline-end]:border-b data-[side=inline-end]:border-s data-[side=inline-start]:-right-[5px] data-[side=inline-start]:border-e data-[side=inline-start]:border-t data-[side=left]:-right-[5px] data-[side=left]:border-e data-[side=left]:border-t data-[side=right]:-left-[5px] data-[side=right]:border-b data-[side=right]:border-s data-[side=top]:-bottom-[5px] data-[side=top]:border-e data-[side=top]:border-b'

// Base UI tooltip, a dark one with short text or with `popover` a light one with a border for longer content.
// The popup has the side it is shown on in data-side.
export default function Tooltip({
  content,
  side = 'top',
  popover = false,
  children
}: {
  content: ReactNode,
  side?: Side,
  popover?: boolean,
  children: ReactElement
}) {
  return (
    <BaseTooltip.Root>
      <BaseTooltip.Trigger render={children} />
      <BaseTooltip.Portal>
        <BaseTooltip.Positioner side={side} sideOffset={popover ? 8 : 4} className="z-1080">
          {popover ? (
            <BaseTooltip.Popup role="tooltip" className="relative max-w-[276px] rounded-md border border-gray-300 bg-white p-4 text-sm text-muted shadow-sm">
              <BaseTooltip.Arrow className={popoverArrowClass} />
              {content}
            </BaseTooltip.Popup>
          ) : (
            <BaseTooltip.Popup role="tooltip" className="relative max-w-[200px] rounded-sm bg-gray-900 px-2 py-1 text-center text-xs text-white">
              <BaseTooltip.Arrow className={`${arrowClass} bg-gray-900`} />
              {content}
            </BaseTooltip.Popup>
          )}
        </BaseTooltip.Positioner>
      </BaseTooltip.Portal>
    </BaseTooltip.Root>
  )
}
