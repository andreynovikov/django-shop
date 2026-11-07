'use client'

import { MouseEventHandler, ReactNode } from 'react'

import { Autocomplete } from '@base-ui/react/autocomplete'

import { menuDividerClass, menuHeaderClass, menuPopupClass } from './menu'

// Base UI autocomplete parts styled as a dropdown menu

const itemClass = 'block w-full truncate px-5 py-1.5 text-sm'

export function AutocompletePopup({ children }: { children: ReactNode }) {
  return (
    <Autocomplete.Portal>
      <Autocomplete.Positioner align="start" className="z-1000">
        <Autocomplete.Popup className={`${menuPopupClass} max-h-[300px] w-(--anchor-width) overflow-y-auto [scrollbar-width:thin]`}>
          {children}
        </Autocomplete.Popup>
      </Autocomplete.Positioner>
    </Autocomplete.Portal>
  )
}

// Prompt, loading or nothing found message shown in place of items
export function AutocompleteStatus({ children }: { children: ReactNode }) {
  return (
    <Autocomplete.Status className={`${itemClass} cursor-default text-gray-500`}>
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
      {separated && <Autocomplete.Separator className={menuDividerClass} />}
      <Autocomplete.Group items={items}>
        {label && <Autocomplete.GroupLabel className={menuHeaderClass}>{label}</Autocomplete.GroupLabel>}
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
    <Autocomplete.Item value={value} onClick={onClick} className={`${itemClass} cursor-pointer text-gray-700 outline-none data-highlighted:bg-dark/9 data-highlighted:text-gray-900`}>
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
