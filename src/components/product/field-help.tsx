'use client'

import { ComponentProps, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Popover } from '@base-ui/react/popover'

import { IconHelp } from '@tabler/icons-react'

import { Spinner } from '@/components/loading'

import { pageKeys, loadPages, loadPage } from '@/lib/queries'

const fieldMappings: Partial<Record<string, string>> = {
  'sm_stitchwidth': 'sm_stitchlength',
  'sm_stitchlenght': 'sm_stitchlength',
}

export default function FieldHelp({ field }: { field: string }) {
  const [open, setOpen] = useState(false)

  const { data: fields } = useQuery({
    queryKey: pageKeys.lists(),
    queryFn: () => loadPages(),
    select: (pages) => pages.filter(page => page.url.startsWith('/help/')).map(page => page.url.replace(/\/help\/(\w+)\/?/, (match, group) => group)),
    placeholderData: []
  })

  const helpPage = fieldMappings[field] ?? (fields?.includes(field) ? field : undefined)
  const uri = ['help', helpPage ?? '']

  const { data, isSuccess } = useQuery({
    queryKey: pageKeys.detail(uri),
    queryFn: () => loadPage(uri),
    enabled: open && helpPage !== undefined
  })

  if (helpPage === undefined)
    return null

  return (
    <Popover.Root open={open} onOpenChange={open => setOpen(open)} modal>
      <Popover.Trigger className="ps-1 align-baseline text-primary">
        <IconHelp size="16" stroke={1.8} className="inline align-baseline" />
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Positioner side="right" sideOffset={8}>
          <Popover.Popup className="box-border h-(--popup-height,auto) w-(--popup-width,auto) max-w-[65vw] origin-(--transform-origin) rounded-lg bg-white px-6 py-4 text-body shadow-lg shadow-black/15 outline outline-black/15 transition-[scale,opacity] duration-150 data-ending-style:scale-90 data-ending-style:opacity-0 data-starting-style:scale-90 data-starting-style:opacity-0 max-lg:max-w-[95vw]">
            <Popover.Arrow className="flex data-[side=bottom]:-top-2 data-[side=left]:-right-[13px] data-[side=left]:rotate-90 data-[side=right]:-left-[13px] data-[side=right]:-rotate-90 data-[side=top]:-bottom-2 data-[side=top]:rotate-180">
              <ArrowSvg />
            </Popover.Arrow>
            <Popover.Viewport className="[&_img]:mb-[0.625em] [&_img]:h-auto [&_img]:max-w-full [&_img[align=left]]:me-[0.625em] [&_img[align=left]]:max-w-[60%]">
              {isSuccess ? (
                <div className="text-xs" dangerouslySetInnerHTML={{ __html: data.content }}></div>
              ) : (
                <Spinner label="Загрузка..." />
              )}
            </Popover.Viewport>
          </Popover.Popup>
        </Popover.Positioner>
      </Popover.Portal>
    </Popover.Root>
  )
}

function ArrowSvg(props: ComponentProps<'svg'>) {
  return (
    <svg width="20" height="10" viewBox="0 0 20 10" fill="none" {...props}>
      <path
        d="M9.66437 2.60207L4.80758 6.97318C4.07308 7.63423 3.11989 8 2.13172 8H0V10H20V8H18.5349C17.5468 8 16.5936 7.63423 15.8591 6.97318L11.0023 2.60207C10.622 2.2598 10.0447 2.25979 9.66437 2.60207Z"
        className="fill-white"
      />
      <path
        d="M8.99542 1.85876C9.75604 1.17425 10.9106 1.17422 11.6713 1.85878L16.5281 6.22989C17.0789 6.72568 17.7938 7.00001 18.5349 7.00001L15.89 7L11.0023 2.60207C10.622 2.2598 10.0447 2.2598 9.66436 2.60207L4.77734 7L2.13171 7.00001C2.87284 7.00001 3.58774 6.72568 4.13861 6.22989L8.99542 1.85876Z"
        className="fill-black/15"
      />
      <path
        d="M10.3333 3.34539L5.47654 7.71648C4.55842 8.54279 3.36693 9 2.13172 9H0V8H2.13172C3.11989 8 4.07308 7.63423 4.80758 6.97318L9.66437 2.60207C10.0447 2.25979 10.622 2.2598 11.0023 2.60207L15.8591 6.97318C16.5936 7.63423 17.5468 8 18.5349 8H20V9H18.5349C17.2998 9 16.1083 8.54278 15.1901 7.71648L10.3333 3.34539Z"
      />
    </svg>
  )
}
