'use client'

import { ReactElement, ReactNode } from 'react'

import { Tooltip as BaseTooltip } from '@base-ui/react/tooltip'

type Side = BaseTooltip.Positioner.State['side']

// Bootstrap 5.0 names horizontal placements start/end
const bootstrapSides: Record<Side, string> = {
  'top': 'top',
  'bottom': 'bottom',
  'left': 'start',
  'right': 'end',
  'inline-start': 'start',
  'inline-end': 'end',
}

// Base UI tooltip rendered with Bootstrap .tooltip markup, the positioner gets .tooltip so the arrow is positioned against it
export default function Tooltip({ content, side = 'top', children }: { content: ReactNode, side?: Side, children: ReactElement }) {
  return (
    <BaseTooltip.Root>
      <BaseTooltip.Trigger render={children} />
      <BaseTooltip.Portal>
        <BaseTooltip.Positioner side={side} className={(state) => `tooltip show bs-tooltip-${bootstrapSides[state.side]}`}>
          <BaseTooltip.Popup className="tooltip-inner">
            <BaseTooltip.Arrow className="tooltip-arrow" />
            {content}
          </BaseTooltip.Popup>
        </BaseTooltip.Positioner>
      </BaseTooltip.Portal>
    </BaseTooltip.Root>
  )
}
