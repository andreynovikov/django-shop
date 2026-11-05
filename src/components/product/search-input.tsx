'use client'

import { useState, useMemo, useDeferredValue } from 'react'
import { useRouter } from 'next/navigation'
import { useQuery, keepPreviousData } from '@tanstack/react-query'

import { Autocomplete } from '@base-ui/react/autocomplete'

import { IconSearch } from '@tabler/icons-react'

import { inputClass } from '@/components/ui/form'
import { AutocompletePopup, AutocompleteStatus, AutocompleteItem, Highlighter } from '@/components/ui/autocomplete'

import { productKeys, loadProductSuggestions } from '@/lib/queries'

const MIN_LENGTH = 3

// Suggests product titles from the backend, a picked title is searched for
export default function ProductSearchInput() {
  const [searchText, setSearchText] = useState('')
  const deferredSearchText = useDeferredValue(searchText)

  const { data: suggestions, isLoading } = useQuery({
    queryKey: productKeys.suggestions(deferredSearchText),
    queryFn: () => loadProductSuggestions(deferredSearchText),
    enabled: searchText.length >= MIN_LENGTH,
    placeholderData: keepPreviousData
  })

  const titles = useMemo(() => {
    if (!suggestions || searchText.length < MIN_LENGTH)
      return []
    return suggestions.results.filter((title, index, all) => all.indexOf(title) === index)
  }, [suggestions, searchText])

  const router = useRouter()

  // the input also changes while moving through suggestions, only typing starts a new search
  const handleValueChange = (value: string, { reason }: Autocomplete.Root.ChangeEventDetails) => {
    if (reason === 'input-change' || reason === 'input-clear')
      setSearchText(value)
  }

  const message =
    searchText.length < MIN_LENGTH ? "Введите строку для поиска..." :
    isLoading ? "Поиск..." :
    titles.length === 0 ? "Ничего не найдено" : null

  return (
    <div className="relative mt-2">
      <form action="/search/">
        <Autocomplete.Root
          items={titles}
          mode="inline"
          onValueChange={handleValueChange}>
          <div className="flex">
            <Autocomplete.Input
              className={`${inputClass()} min-w-0 flex-1 rounded-e-none`}
              name="text"
              placeholder="Поиск товаров" />
            <button className="-ms-px flex items-center rounded-e-md border bg-light px-3 py-1.5 text-body" type="submit">
              <IconSearch />
            </button>
          </div>
          <AutocompletePopup>
            {message && <AutocompleteStatus>{message}</AutocompleteStatus>}
            <Autocomplete.List>
              {(title: string) => (
                <AutocompleteItem
                  key={title}
                  value={title}
                  onClick={() => router.push(`/search/?${new URLSearchParams({ text: title })}`)}>
                  <Highlighter search={searchText}>{title}</Highlighter>
                </AutocompleteItem>
              )}
            </Autocomplete.List>
          </AutocompletePopup>
        </Autocomplete.Root>
      </form>
    </div>
  )
}
