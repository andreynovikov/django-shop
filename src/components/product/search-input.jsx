import { useState, useEffect, useMemo, useDeferredValue } from 'react';
import { useRouter } from 'next/router';
import { useQuery } from 'react-query';

import { productKeys, loadProductSuggestions } from '@/lib/queries';

export default function ProductSearchInput() {
    const [searchText, setSearchText] = useState('');
    const [focused, setFocused] = useState(false);
    const deferredSearchText = useDeferredValue(searchText);

    const router = useRouter();

    useEffect(() => {
        if (router.query.text !== undefined)
            setSearchText(router.query.text);
    }, [router.query.text]);

    const { data: titles } = useQuery(
        productKeys.suggestions(deferredSearchText),
        () => loadProductSuggestions(deferredSearchText),
        {
            enabled: searchText.length > 2,
            keepPreviousData : true
        }
    );

    const suggest = (text) => {
        setSearchText(text);
    };

    const handleBlur = () => {
        setTimeout(() => { // otherwise click on suggestion is dismissed
            setFocused(false);
        }, 100);
    };

    const suggestions = useMemo(() =>
        titles && titles.count > 1 && titles.results.map((title) => (
            <a className="dropdown-item" key={title} onClick={() => suggest(title)} style={{ cursor: "pointer" }}>{ title }</a>
        )),
        [titles]
    );

    return (
        <div className="position-relative w-100 mx-4">
            <form className="input-group d-none d-lg-flex" action="/search/">
                <input
                    className="form-control product-search rounded-end pe-5"
                    name="text"
                    type="text"
                    placeholder="Поиск товаров"
                    autoComplete="off"
                    value={searchText}
                    onChange={(e) => setSearchText(e.target.value)}
                    onFocus={() => setFocused(true)}
                    onBlur={handleBlur} />
                <i className="ci-search position-absolute top-50 end-0 translate-middle-y text-muted fs-base me-3" />
            </form>
            <div className={"dropdown-menu" + (focused && searchText.length > 2 && titles && titles.count > 1 ? " d-block" : "")}>
                { suggestions }
            </div>
        </div>
    )
}
