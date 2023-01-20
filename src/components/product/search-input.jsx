import { useState, useMemo, useDeferredValue } from 'react';
import { useQuery } from 'react-query';

import { AsyncTypeahead } from 'react-bootstrap-typeahead';

import { productKeys, loadProductSuggestions } from '@/lib/queries';

export default function ProductSearchInput() {
    const [searchText, setSearchText] = useState('');
    const deferredSearchText = useDeferredValue(searchText);

    const { data: titles, isLoading } = useQuery(
        productKeys.suggestions(deferredSearchText),
        () => loadProductSuggestions(deferredSearchText),
        {
            enabled: searchText.length > 0,
            keepPreviousData : true
        }
    );

    const options = useMemo(() => (
        titles && titles.count > 0 && titles.results.filter((x, i, a) => a.indexOf(x) == i) || []
    ), [titles]);

    return (
        <div className="position-relative mt-2">
            <form action="/search/">
                <AsyncTypeahead
                    id="product-search-input"
                    filterBy={() => true}
                    isLoading={isLoading}
                    minLength={3}
                    onSearch={(query) => setSearchText(query)}
                    options={options}
                    placeholder="Поиск товаров"
                    promptText="Введите строку для поиска..."
                    searchText="Поиск..."
                    renderInput={({ inputRef, referenceElementRef, ...inputProps }) => (
                        <div className="input-group">
                            <input
                                {...inputProps}
                                ref={(input) => {
                                    inputRef(input);
                                    referenceElementRef(input);
                                }}
                                onKeyUp={(e) => {
                                    if (e.key === "Enter") e.currentTarget.form.submit();
                                }}
                                className="form-control"
                                name="text"
                                style={{height: 'inherit'}}
                            />
                            <button className="input-group-text" type="submit">
                                Найти
                            </button>
                        </div>
                    )}
                />
            </form>
        </div>
    )
}
