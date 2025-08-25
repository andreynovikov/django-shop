'use client'

import { useState, useMemo, useDeferredValue } from 'react'
import { useRouter } from 'next/router'
import { useQuery, keepPreviousData } from '@tanstack/react-query'

import { AsyncTypeahead, Menu, MenuItem, Highlighter } from 'react-bootstrap-typeahead'

import { productKeys } from '@/lib/queries'
import { loadProductSuggestions } from '@/lib/diginetica'

function renderMenu(
    results,
    {
        newSelectionPrefix,
        paginationText,
        renderMenuItemChildren,
        ...menuProps
    },
    state
) {
    const items = results.reduce((items, item, index, results) => {
        if (item.section === 'correction')
            items.push(
                <MenuItem key={`correction:${item.label}`} option={item} position={index}>
                    <Highlighter search={state.text}>{item.label}</Highlighter>
                </MenuItem>
            )
        if (item.section === 'sts') {
            if (index === 0 || results.at(index - 1).section !== 'sts') {
                if (index > 0)
                    items.push(<Menu.Divider key="sts-divider" />)
                items.push(
                    <Menu.Header key="sts">Часто ищут</Menu.Header>
                )
            }
            items.push(
                <MenuItem key={`sts:${item.label}`} option={item} position={index}>
                    <i className="ci-search text-muted fs-sm me-2" />
                    <Highlighter search={state.text}>{item.label}</Highlighter>
                </MenuItem>
            )
        }

        if (item.section === 'products') {
            if (index === 0 || results.at(index - 1).section !== 'products') {
                if (index > 0)
                    items.push(<Menu.Divider key="products-divider" />)
                items.push(
                    <Menu.Header key="products">Популярные товары</Menu.Header>
                )
            }
            items.push(
                <MenuItem key={`products:${item.product.id}`} option={item} position={index}>
                    <div className="d-flex align-items-center gap-2">
                        <div style={{ width: "64px" }}>
                            {item.product.image_url ? <img src={item.product.image_url} className="img-fluid" /> : "no img"}
                        </div>
                        <div className="d-flex flex-column">
                            <div>
                                <Highlighter search={state.text}>{item.product.name}</Highlighter>
                            </div>
                            <div>
                                {(+item.product.price).toLocaleString('ru')}<small>&nbsp;руб</small>
                            </div>
                        </div>
                    </div>
                </MenuItem>
            )
        }

        return items
    }, [])

    return <Menu {...menuProps}>{items}</Menu>
}

export default function ProductSearchInput({ mobile = false }) {
    const [searchText, setSearchText] = useState('')
    const deferredSearchText = useDeferredValue(searchText)

    const { data: suggestions, isLoading } = useQuery({
        queryKey: productKeys.suggestions(deferredSearchText),
        queryFn: () => loadProductSuggestions(deferredSearchText),
        enabled: searchText.length > 2,
        placeholderData: keepPreviousData
    })

    const options = useMemo(() => {
        if (!suggestions)
            return []

        const options = []

        suggestions.correction && options.push(
            {
                section: 'correction',
                label: suggestions.correction
            }
        )

        suggestions.sts && suggestions.sts.forEach(st => options.push(
            {
                section: 'sts',
                label: st.st
            }
        ))

        suggestions.products && suggestions.products.forEach(product => options.push(
            {
                section: 'products',
                label: product.name,
                product
            }
        ))

        return options
    }, [suggestions])

    const router = useRouter()

    const handleSelectionChange = (selected) => {
        if (selected.length === 0)
            return
        if (selected[0].section === 'products')
            router.push(selected[0].product.link_url.replace('.html', '/'))
    }

    return (
        <form className="w-100" action="/search/">
            <AsyncTypeahead
                id={"product-search-input" + (mobile ? "-mobile" : "")}
                className="w-100"
                filterBy={() => true}
                isLoading={isLoading}
                minLength={3}
                onSearch={(query) => setSearchText(query)}
                onChange={handleSelectionChange}
                options={options}
                placeholder="Поиск товаров"
                promptText="Введите строку для поиска..."
                searchText="Ищем..."
                emptyLabel="Ничего не найдено"
                renderMenu={renderMenu}
                renderInput={({ inputRef, referenceElementRef, ...inputProps }) => (
                    <div className="input-group">
                        {mobile && <i className="ci-search position-absolute top-50 start-0 translate-middle-y text-muted fs-base ms-3" />}
                        <input
                            {...inputProps}
                            ref={(input) => {
                                inputRef(input)
                                referenceElementRef(input)
                            }}
                            onKeyUp={(e) => {
                                if (e.key === "Enter") e.currentTarget.form.submit()
                            }}
                            className={"form-control pe-5 " + (mobile ? "rounded-start" : "rounded-end")}
                            name="text"
                        />
                        {!mobile && (
                            <button className="btn btn-link position-absolute top-50 end-0 translate-middle-y p-0 me-3" type="submit">
                                <i className="ci-search text-muted fs-base" />
                            </button>
                        )}
                    </div>
                )}
            />
        </form>
    )
}
