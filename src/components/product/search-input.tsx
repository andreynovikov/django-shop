'use client'

import { useState, useMemo, useDeferredValue } from 'react'
import { useRouter } from 'next/navigation'
import { useQuery, keepPreviousData } from '@tanstack/react-query'

import { Autocomplete } from '@base-ui/react/autocomplete'
import { IconSearch } from '@tabler/icons-react'

import { inputClass } from '@/components/ui/form'
import { AutocompletePopup, AutocompleteStatus, AutocompleteGroup, AutocompleteItem, Highlighter } from '@/components/ui/autocomplete'

import { productKeys } from '@/lib/queries'
import { loadProductSuggestions, ProductResult } from '@/lib/diginetica'

const MIN_LENGTH = 3

type SuggestionItem =
  | { section: 'correction' | 'sts', label: string }
  | { section: 'products', label: string, product: ProductResult }

interface SuggestionGroup {
  section: SuggestionItem['section']
  label?: string
  items: SuggestionItem[]
}

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

    const allGroups: SuggestionGroup[] = [
      {
        section: 'correction',
        items: suggestions.correction ? [{ section: 'correction', label: suggestions.correction }] : []
      },
      {
        section: 'sts',
        label: 'Часто ищут',
        items: (suggestions.sts ?? []).map(st => ({ section: 'sts', label: st.st }))
      },
      {
        section: 'products',
        label: 'Популярные товары',
        items: (suggestions.products ?? []).map(product => ({ section: 'products', label: product.name, product }))
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
                {(item) => item.section === 'products' ? (
                  <AutocompleteItem
                    key={`products:${item.product.id}`}
                    value={item}
                    onClick={() => router.push(item.product.link_url.replace('.html', '/'))}>
                    <div className="flex items-center gap-2">
                      <div className="w-16 shrink-0">
                        {/* Diginetica's image host isn't in images.remotePatterns, the name next to it describes the product */}
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        {item.product.image_url ? <img src={item.product.image_url} className="h-auto max-w-full" alt="" /> : "no img"}
                      </div>
                      <div className="flex min-w-0 flex-col">
                        <div>
                          <Highlighter search={searchText}>{item.product.name}</Highlighter>
                        </div>
                        <div>
                          {(+item.product.price).toLocaleString('ru')}<small>&nbsp;руб</small>
                        </div>
                      </div>
                    </div>
                  </AutocompleteItem>
                ) : (
                  <AutocompleteItem
                    key={`${item.section}:${item.label}`}
                    value={item}
                    onClick={item.section === 'sts' ? () => router.push(`/search/?${new URLSearchParams({ text: item.label })}`) : undefined}>
                    {item.section === 'sts' && <IconSearch size={14} stroke={1.5} className="me-2 align-[-2px] text-muted" />}
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
