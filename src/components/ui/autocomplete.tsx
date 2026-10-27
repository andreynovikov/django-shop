'use client'

import { MouseEventHandler, ReactNode } from 'react'

import { Autocomplete } from '@base-ui/react/autocomplete'

// Base UI autocomplete parts rendered with Bootstrap .dropdown-menu markup, see .sw-autocomplete-menu in styles.scss

export function AutocompletePopup({ children }: { children: ReactNode }) {
  return (
    <Autocomplete.Portal>
      <Autocomplete.Positioner align="start">
        <Autocomplete.Popup className="dropdown-menu show sw-autocomplete-menu">
          {children}
        </Autocomplete.Popup>
      </Autocomplete.Positioner>
    </Autocomplete.Portal>
  )
}

// Prompt, loading or nothing found message shown in place of items
export function AutocompleteStatus({ children }: { children: ReactNode }) {
  return (
    <Autocomplete.Status className="dropdown-item disabled">
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
      {separated && <Autocomplete.Separator className="dropdown-divider" />}
      <Autocomplete.Group items={items}>
        {label && <Autocomplete.GroupLabel className="dropdown-header">{label}</Autocomplete.GroupLabel>}
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
    // highlighted items are styled by [data-highlighted], Cartzilla's .dropdown-item.active isn't clickable
    <Autocomplete.Item value={value} onClick={onClick} className="dropdown-item">
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
    index % 2 === 1 ? <mark className="sw-highlight-text" key={index}>{part}</mark> : part
  )
}
