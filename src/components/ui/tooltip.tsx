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

// Base UI tooltip rendered with Bootstrap .tooltip markup, the positioner gets .tooltip so the arrow is positioned against it.
// The arrow is a sibling of .tooltip-inner as in Bootstrap, inside it the centered text would shift the arrow triangle.
// With `popover` it is rendered with Bootstrap .popover markup instead, Bootstrap styles .popover-arrow only as a direct child
// of .popover so the popup gets .popover and is taken out of absolute positioning to stay inside the positioner.
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
        {popover ? (
          <BaseTooltip.Positioner side={side} sideOffset={8}>
            <BaseTooltip.Popup className={(state) => `popover bs-popover-${bootstrapSides[state.side]}`} style={{ position: 'relative' }}>
              <BaseTooltip.Arrow className="popover-arrow" />
              <div className="popover-body">
                {content}
              </div>
            </BaseTooltip.Popup>
          </BaseTooltip.Positioner>
        ) : (
          <BaseTooltip.Positioner side={side} className={(state) => `tooltip show bs-tooltip-${bootstrapSides[state.side]}`}>
            <BaseTooltip.Arrow className="tooltip-arrow" />
            <BaseTooltip.Popup className="tooltip-inner">
              {content}
            </BaseTooltip.Popup>
          </BaseTooltip.Positioner>
        )}
      </BaseTooltip.Portal>
    </BaseTooltip.Root>
  )
}
