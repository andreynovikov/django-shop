'use client'

import { MouseEventHandler, ReactNode } from 'react'

import { Autocomplete } from '@base-ui/react/autocomplete'

// Base UI autocomplete parts styled as a dropdown menu

const itemClass = 'block w-full truncate px-4 py-1'

export function AutocompletePopup({ children }: { children: ReactNode }) {
  return (
    <Autocomplete.Portal>
      <Autocomplete.Positioner align="start">
        <Autocomplete.Popup className="relative z-1000 max-h-[300px] w-(--anchor-width) min-w-40 overflow-y-auto rounded-md border border-black/15 bg-white py-2 text-left text-body [&::-webkit-scrollbar]:bg-light">
          {children}
        </Autocomplete.Popup>
      </Autocomplete.Positioner>
    </Autocomplete.Portal>
  )
}

// Prompt, loading or nothing found message shown in place of items
export function AutocompleteStatus({ children }: { children: ReactNode }) {
  return (
    <Autocomplete.Status className={`${itemClass} cursor-default text-gray-400`}>
      {children}
    </Autocomplete.Status>
  )
}

export function AutocompleteGroup<Item>({
  label,
  items,
  separated = false,
  children
}: {
  label?: ReactNode,
  items: readonly Item[],
  separated?: boolean,
  children: (item: Item, index: number) => ReactNode
}) {
  return (
    <>
      {separated && <Autocomplete.Separator className="my-2 border-t border-black/15" />}
      <Autocomplete.Group items={items}>
        {label && <Autocomplete.GroupLabel className="block px-4 py-2 text-xs whitespace-nowrap text-secondary">{label}</Autocomplete.GroupLabel>}
        <Autocomplete.Collection>
          {children}
        </Autocomplete.Collection>
      </Autocomplete.Group>
    </>
  )
}

export function AutocompleteItem({
  value,
  onClick,
  children
}: {
  value: unknown,
  onClick?: MouseEventHandler<HTMLDivElement>,
  children: ReactNode
}) {
  return (
    <Autocomplete.Item value={value} onClick={onClick} className={`${itemClass} cursor-pointer text-primary outline-none data-highlighted:bg-light`}>
      {children}
    </Autocomplete.Item>
  )
}

// Marks every case insensitive occurrence of the search text
export function Highlighter({ search, children }: { search: string, children: string }) {
  if (!search)
    return children

  const escaped = search.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  return children.split(new RegExp(`(${escaped})`, 'gi')).map((part, index) =>
    index % 2 === 1 ? <mark className="bg-inherit p-0 font-bold text-inherit" key={index}>{part}</mark> : part
  )
}
