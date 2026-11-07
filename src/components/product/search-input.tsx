'use client'

import { useState, useMemo, useDeferredValue } from 'react'
import { useRouter } from 'next/navigation'
import { useQuery, keepPreviousData } from '@tanstack/react-query'

import { Autocomplete } from '@base-ui/react/autocomplete'
import { IconSearch } from '@tabler/icons-react'

import { inputClass } from '@/components/ui/form'
import { AutocompletePopup, AutocompleteStatus, AutocompleteGroup, AutocompleteItem, Highlighter } from '@/components/ui/autocomplete'

import { productKeys, loadProductSuggestions } from '@/lib/queries'

const MIN_LENGTH = 3

interface SuggestionItem {
  section: 'sts'
  label: string
}

interface SuggestionGroup {
  section: SuggestionItem['section']
  label: string
  items: SuggestionItem[]
}

// Suggests product titles from the backend, a picked title is searched for
export default function ProductSearchInput({ mobile = false }: { mobile?: boolean }) {
  const [searchText, setSearchText] = useState('')
  const deferredSearchText = useDeferredValue(searchText)

  const { data: suggestions, isLoading } = useQuery({
    queryKey: productKeys.suggestions(deferredSearchText),
    queryFn: () => loadProductSuggestions(deferredSearchText),
    enabled: searchText.length >= MIN_LENGTH,
    placeholderData: keepPreviousData
  })

  const groups = useMemo(() => {
    if (!suggestions || searchText.length < MIN_LENGTH)
      return []

    const titles = suggestions.results.filter((title, index, all) => all.indexOf(title) === index)
    const allGroups: SuggestionGroup[] = [
      {
        section: 'sts',
        label: 'Часто ищут',
        items: titles.map(title => ({ section: 'sts', label: title }))
      },
    ]
    return allGroups.filter(group => group.items.length > 0)
  }, [suggestions, searchText])

  const router = useRouter()

  // the input also changes while moving through suggestions, only typing starts a new search
  const handleValueChange = (value: string, { reason }: Autocomplete.Root.ChangeEventDetails) => {
    if (reason === 'input-change' || reason === 'input-clear')
      setSearchText(value)
  }

  const message =
    searchText.length < MIN_LENGTH ? "Введите строку для поиска..." :
    isLoading ? "Ищем..." :
    groups.length === 0 ? "Ничего не найдено" : null

  return (
    <form className="w-full" action="/search/">
      <Autocomplete.Root
        items={groups}
        mode="inline"
        itemToStringValue={(item) => item.label}
        onValueChange={handleValueChange}>
        <div className="relative">
          {mobile && <IconSearch size={16} stroke={1.5} className="absolute top-1/2 left-0 z-5 ms-4 -translate-y-1/2 text-muted" />}
          <Autocomplete.Input
            className={`${inputClass()} ${mobile ? 'ps-10' : 'pe-12'}`}
            name="text"
            placeholder="Поиск товаров" />
          {mobile ? (
            // Base UI adds a hidden input, without a submit button a form with two inputs isn't submitted by Enter
            <button className="sr-only" type="submit" tabIndex={-1} aria-hidden="true" />
          ) : (
            <button className="absolute top-1/2 right-0 me-4 -translate-y-1/2 p-0 text-muted" type="submit" aria-label="Найти">
              <IconSearch size={16} stroke={1.5} className="block" />
            </button>
          )}
        </div>
        <AutocompletePopup>
          {message && <AutocompleteStatus>{message}</AutocompleteStatus>}
          <Autocomplete.List>
            {(group: SuggestionGroup, index: number) => (
              <AutocompleteGroup key={group.section} label={group.label} items={group.items} separated={index > 0}>
                {(item) => (
                  <AutocompleteItem
                    key={`${item.section}:${item.label}`}
                    value={item}
                    onClick={() => router.push(`/search/?${new URLSearchParams({ text: item.label })}`)}>
                    <IconSearch size={14} stroke={1.5} className="me-2 align-[-2px] text-muted" />
                    <Highlighter search={searchText}>{item.label}</Highlighter>
                  </AutocompleteItem>
                )}
              </AutocompleteGroup>
            )}
          </Autocomplete.List>
        </AutocompletePopup>
      </Autocomplete.Root>
    </form>
  )
}
