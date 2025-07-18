import { useState, useMemo, useDeferredValue } from 'react';
import { useQuery, keepPreviousData } from '@tanstack/react-query';

import { AsyncTypeahead } from 'react-bootstrap-typeahead';

import { productKeys, loadProductSuggestions } from '@/lib/queries';

export default function ProductSearchInput({ mobile=false }) {
    const [searchText, setSearchText] = useState('');
    const deferredSearchText = useDeferredValue(searchText);

    const { data: titles, isLoading } = useQuery({
        queryKey: productKeys.suggestions(deferredSearchText),
        queryFn: () => loadProductSuggestions(deferredSearchText),
        enabled: searchText.length > 2,
        placeholderData: keepPreviousData
    });

    const options = useMemo(() => (
        titles && titles.count > 0 && titles.results.filter((x, i, a) => a.indexOf(x) == i) || []
    ), [titles]);

    return (
        <form className="w-100" action="/search/">
            <AsyncTypeahead
                id={"product-search-input" + (mobile ? "-mobile" : "")}
                className="w-100"
                filterBy={() => true}
                isLoading={isLoading}
                minLength={3}
                onSearch={(query) => setSearchText(query)}
                options={options}
                placeholder="Поиск товаров"
                promptText="Введите строку для поиска..."
                searchText="Ищем..."
                emptyLabel="Ничего не найдено"
                renderInput={({ inputRef, referenceElementRef, ...inputProps }) => (
                    <div className="input-group">
                        { mobile && <i className="ci-search position-absolute top-50 start-0 translate-middle-y text-muted fs-base ms-3" /> }
                        <input
                            {...inputProps}
                            ref={(input) => {
                                inputRef(input);
                                referenceElementRef(input);
                            }}
                            onKeyUp={(e) => {
                                if (e.key === "Enter") e.currentTarget.form.submit();
                            }}
                            className={"form-control pe-5 " + (mobile ? "rounded-start" : "rounded-end")}
                            name="text"
                        />
                        { !mobile && (
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
