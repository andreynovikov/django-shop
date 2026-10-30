'use client'

import { useState, useMemo, useDeferredValue } from 'react'
import { useQuery, keepPreviousData } from '@tanstack/react-query'

import { Autocomplete } from '@base-ui/react/autocomplete'

import { AutocompletePopup, AutocompleteStatus, AutocompleteGroup, AutocompleteItem, Highlighter } from '@/components/ui/autocomplete'

import { useNavigation } from '@/lib/navigation'
import { productKeys } from '@/lib/queries'
import { loadProductSuggestions } from '@/lib/diginetica'

const MIN_LENGTH = 3

export default function ProductSearchInput({ mobile = false }) {
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

    return [
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
    ].filter(group => group.items.length > 0)
  }, [suggestions, searchText])

  const { navigate } = useNavigation()

  // the input also changes while moving through suggestions, only typing starts a new search
  const handleValueChange = (value, { reason }) => {
    if (reason === 'input-change' || reason === 'input-clear')
      setSearchText(value)
  }

  const message =
    searchText.length < MIN_LENGTH ? "Введите строку для поиска..." :
    isLoading ? "Ищем..." :
    groups.length === 0 ? "Ничего не найдено" : null

  return (
    <form className="w-100" action="/search/">
      <Autocomplete.Root
        items={groups}
        mode="inline"
        itemToStringValue={(item) => item.label}
        onValueChange={handleValueChange}>
        <div className="input-group">
          {mobile && <i className="ci-search position-absolute top-50 start-0 translate-middle-y text-muted fs-base ms-3" />}
          <Autocomplete.Input
            className={"form-control pe-5 " + (mobile ? "rounded-start" : "rounded-end")}
            name="text"
            placeholder="Поиск товаров" />
          {mobile ? (
            // Base UI adds a hidden input, without a submit button a form with two inputs isn't submitted by Enter
            <button className="visually-hidden" type="submit" tabIndex={-1} aria-hidden="true" />
          ) : (
            <button className="btn btn-link position-absolute top-50 end-0 translate-middle-y p-0 me-3" type="submit">
              <i className="ci-search text-muted fs-base" />
            </button>
          )}
        </div>
        <AutocompletePopup>
          {message && <AutocompleteStatus>{message}</AutocompleteStatus>}
          <Autocomplete.List>
            {(group, index) => (
              <AutocompleteGroup key={group.section} label={group.label} items={group.items} separated={index > 0}>
                {(item) => item.section === 'products' ? (
                  <AutocompleteItem
                    key={`products:${item.product.id}`}
                    value={item}
                    onClick={() => navigate(item.product.link_url.replace('.html', '/'))}>
                    <div className="d-flex align-items-center gap-2">
                      <div style={{ width: "64px" }}>
                        {item.product.image_url ? <img src={item.product.image_url} className="img-fluid" /> : "no img"}
                      </div>
                      <div className="d-flex flex-column">
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
                    onClick={item.section === 'sts' ? () => navigate(`/search/?${new URLSearchParams({ text: item.label })}`) : undefined}>
                    {item.section === 'sts' && <i className="ci-search text-muted fs-sm me-2" />}
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
