import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useQuery } from 'react-query';

import Link from 'next/link';

import { categoryKeys, loadCategories } from '@/lib/queries';
import { columns, rows } from '@/lib/partition';

const first = [14,15,16,17];
const other = [339,473,324,14,15,16,17]; // other than these

export default function Catalog({visible, setVisible, buttonRef}) {
    const [ready, setReady] = useState(false);
    const [categoryNew, setCategoryNew] = useState(null);
    const [categoryPromo, setCategoryPromo] = useState(null);
    const [categoryDiscount, setCategoryDiscount] = useState(null);

    const ref = useRef();

    const router = useRouter();

    useEffect(() => {
        const handleRouteChange = () => {
            setVisible(false);
        };
        router.events.on('routeChangeStart', handleRouteChange);
        return () => {
            router.events.off('routeChangeStart', handleRouteChange)
        }
    }, [router.events, setVisible]);

    useEffect(() => {
        function handleClickOutside(event) {
            if (!ref.current?.contains(event.target) && !buttonRef.current?.contains(event.target)) {
                setVisible(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, [setVisible]);

    const { data: categories, isSuccess } = useQuery(
        categoryKeys.lists(),
        () => loadCategories()
    );

    useEffect(() => {
        if (isSuccess) {
            for (const category of categories) {
                if (category.slug === 'New')
                    setCategoryNew(category);
                if (category.slug === 'promo')
                    setCategoryPromo(category);
                if (category.slug === 'Discount')
                    setCategoryDiscount(category);
            }
            setReady(true);
        }
    }, [isSuccess, categories]);

    return (
        <div className={"position-relative" + (visible ? "" : " d-none")} ref={ref}>
            <div className="sw-catalog">
                { ready && (
                    <>
                        <div className="d-flex flex-wrap flex-md-nowrap justify-content-between mb-4">
                            <Link className="w-100 d-flex align-items-center bg-faded-info rounded-3 py-2 ps-2 mb-4 mx-2" href={`/catalog/${categoryNew.slug}/`}>
                                { categoryNew.image && <img className="sw-category-image" src={categoryNew.image} alt={categoryNew.name} /> }
                                <div className="py-4 px-3">
                                    <div className="h5 mb-2">{categoryNew.name}</div>
                                    <div className="text-info fs-sm">Посмотреть все<i className="ci-arrow-right fs-xs ms-1" /></div>
                                </div>
                            </Link>
                            <Link className="w-100 d-flex align-items-center bg-faded-warning rounded-3 py-2 ps-2 mb-4 mx-2" href={`/catalog/${categoryPromo.slug}/`}>
                                { categoryPromo.image && <img className="sw-category-image" src={categoryPromo.image} alt={categoryPromo.name} /> }
                                <div className="py-4 px-3">
                                    <div className="h5 mb-2">{categoryPromo.name}</div>
                                    <div className="text-warning fs-sm">Посмотреть все<i className="ci-arrow-right fs-xs ms-1" /></div>
                                </div>
                            </Link>
                        </div>

                        {columns(categories.filter(category => first.includes(category.id)), 2).map((column, index) => (
                            <div className="d-flex flex-wrap flex-md-nowrap" key={index}>
                                {column.map((category) => (
                                    <div className="w-100 mb-3 mx-4" key={category.id}>
                                        <div className="h6 mb-3">
                                            <Link href={`/catalog/${category.slug}/`}>
                                                { category.svg_icon && <span className="sw-catalog-icon me-1" dangerouslySetInnerHTML={{__html: category.svg_icon }}></span> }
                                                {category.name}
                                            </Link>
                                        </div>
                                        { category.children && (
                                            <div className="ms-4">
                                                <div className="widget widget-links">
                                                    <ul className="widget-list">
                                                        {category.children.map((subcategory) => (
                                                            <li className="widget-list-item pb-1" key={subcategory.id}>
                                                                <Link className="widget-list-link" href={`/catalog/${category.slug}/${subcategory.slug}/`}>
                                                                    {subcategory.name}
                                                                </Link>
                                                            </li>
                                                        ))}
                                                    </ul>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        ))}

                        {categories.filter(category => !other.includes(category.id)).map((category, index) => (
                            <div className={"mx-4 mb-3" + (index === 0 ? " mt-4" : "")} key={category.id}>
                                <div className="h7 mb-3">
                                    <Link href={`/catalog/${category.slug}/`}>
                                        { category.svg_icon && <span className="sw-catalog-icon me-1" dangerouslySetInnerHTML={{__html: category.svg_icon }}></span> }
                                        {category.name}
                                    </Link>
                                </div>
                                { category.children && (
                                    <div className="d-flex flex-wrap flex-md-nowrap">
                                        {rows(category.children, 2).map((row, index, arr) => (
                                            <div className={"w-100 mx-4" + (index === arr.length - 1 ? " pb-2" : "")} key={index}>
                                                <div className={"widget widget-links" + (index === arr.length - 1 ? " ms-md-4" : "")}>
                                                    <ul className="widget-list">
                                                        {row.map((subcategory) => (
                                                            <li className="widget-list-item pb-1 mb-1" key={subcategory.id}>
                                                                <Link className="widget-list-link" href={`/catalog/${category.slug}/${subcategory.slug}/`}>
                                                                    {subcategory.name}
                                                                </Link>
                                                            </li>
                                                        ))}
                                                    </ul>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        ))}

                        <div className="d-flex flex-wrap flex-md-nowrap justify-content-between mt-4">
                            <Link className="w-100 d-flex align-items-center bg-faded-success rounded-3 py-2 ps-2 mx-2" href={`/catalog/${categoryDiscount.slug}/`}>
                                { categoryDiscount.image && <img className="sw-category-image" src={categoryDiscount.image} alt={categoryDiscount.name} /> }
                                <div className="py-4 px-3">
                                    <div className="h5 mb-2">{categoryDiscount.name}</div>
                                    <div className="text-success fs-sm">Посмотреть все<i className="ci-arrow-right fs-xs ml-1" /></div>
                                </div>
                            </Link>
                            <div className="d-none d-lg-flex w-100 py-2 ps-2 mx-2"></div>
                        </div>
                    </>
                )}
            </div>
        </div>
    )
}
