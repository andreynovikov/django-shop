import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { useQuery } from 'react-query';

import { withClient, categoryKeys, loadCategories, loadCategory } from '@/lib/queries';
import { columns, rows } from '@/lib/partition';

import styles from './catalog.module.css';

const first = [14,15,16,17];
const other = [339,473,324,14,15,16,17]; // other than these

export default function Catalog({visible, setVisible, buttonRef}) {
    const [ready, setReady] = useState(false);
    const [categoryNew, setCategoryNew] = useState(null);
    const [categoryPromo, setCategoryPromo] = useState(null);
    const [categoryDiscount, setCategoryDiscount] = useState(null);

    const ref = useRef(null);

    const router = useRouter();

    useEffect(() => {
        const handleRouteChange = (url) => {
            setVisible(false);
        };
        router.events.on('routeChangeStart', handleRouteChange);
        return () => {
            router.events.off('routeChangeStart', handleRouteChange)
        }
    }, [router.events]);

    useEffect(() => {
        function handleClickOutside(event) {
            if (ref.current && !ref.current.contains(event.target) && !buttonRef.current?.contains(event.target)) {
                setVisible(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, [ref]);

    const { data: categories, isSuccess } = useQuery(
        categoryKeys.lists(),
        () => withClient(loadCategories)
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
    }, [isSuccess]);

    return (
        <div className="container" style={{position: "relative"}} ref={ref}>
            { visible && (
                <div className={"card border-0 shadow " + styles.catalog}>
                    <div className="card-body">

                        { ready && (
                            <>
                                <div className="d-flex flex-wrap flex-md-nowrap justify-content-between mb-4">
                                    <Link href={`/catalog/${categoryNew.slug}/`}>
                                        <a className="d-flex w-100 align-items-center bg-faded-info rounded-3 py-2 ps-2 mb-4 mx-2">
                                            <img src="/media/cache/aa/a0/aaa0178369c842e19ba0512cb7ff4c01.jpg" width="120" heigth="120" />
                                            <div className="py-4 px-3">
                                                <div className="h5 mb-2">{categoryNew.name}</div>
                                                <div className="text-info fs-sm">Посмотреть все<i className="ci-arrow-right fs-xs ms-1" /></div>
                                            </div>
                                        </a>
                                    </Link>
                                    <Link href={`/catalog/${categoryPromo.slug}/`}>
                                        <a className="d-flex w-100 align-items-center bg-faded-warning rounded-3 py-2 ps-2 mb-4 mx-2">
                                            <img src="/media/cache/c6/e3/c6e33af587fa52efda6f766832ea5781.jpg" width="120" heigth="120" />
                                            <div className="py-4 px-3">
                                                <div className="h5 mb-2">{categoryPromo.name}</div>
                                                <div className="text-warning fs-sm">Посмотреть все<i className="ci-arrow-right fs-xs ms-1" /></div>
                                            </div>
                                        </a>
                                    </Link>
                                </div>

                                {columns(categories.filter(category => first.includes(category.id)), 2).map((column, index) => (
                                    <div className="d-flex flex-wrap flex-md-nowrap" key={index}>
                                        {column.map((category, index) => (
                                            <div className="w-100 mb-3 mx-4" key={category.id}>
                                                <div className="h6 mb-3">
                                                    <Link href={`/catalog/${category.slug}/`}>
                                                        <a><i className="ci-printer opacity-60 fs-lg mt-n1 me-2" />{category.name}</a>
                                                    </Link>
                                                </div>
                                                { category.children && (
                                                    <div className="ms-4">
                                                        <div className="widget widget-links">
                                                            <ul className="widget-list">
                                                                {category.children.map((subcategory, index) => (
                                                                    <li className="widget-list-item pb-1" key={subcategory.id}>
                                                                        <Link href={`/catalog/${category.slug}/${subcategory.slug}/`}>
                                                                            <a className="widget-list-link">{subcategory.name}</a>
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
                                                <a><i className="ci-printer opacity-60 fs-lg mt-n1 me-2" />{category.name}</a>
                                            </Link>
                                        </div>
                                        { category.children && (
                                            <div className="d-flex flex-wrap flex-md-nowrap">
                                                {rows(category.children, 2).map((row, index, arr) => (
                                                    <div className={"w-100 mx-4" + (index === arr.length - 1 ? " pb-2" : "")} key={index}>
                                                        <div className={"widget widget-links" + (index === arr.length - 1 ? " ms-md-4" : "")}>
                                                            <ul className="widget-list">
                                                                {row.map((subcategory, index) => (
                                                                    <li className="widget-list-item pb-1 mb-1" key={subcategory.id}>
                                                                        <Link href={`/catalog/${category.slug}/${subcategory.slug}/`}>
                                                                            <a className="widget-list-link">{subcategory.name}</a>
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
                                    <Link href={`/catalog/${categoryDiscount.slug}/`}>
                                        <a className="d-flex w-100 align-items-center bg-faded-success rounded-3 py-2 ps-2 mb-4 mx-2">
                                            <img src="/media/cache/50/19/501981b1acd8936ed6c3cd6709356a62.jpg" width="120" heigth="120" />
                                            <div className="py-4 px-3">
                                                <div className="h5 mb-2">{categoryDiscount.name}</div>
                                                <div className="text-success fs-sm">Посмотреть все<i className="ci-arrow-right fs-xs ml-1" /></div>
                                            </div>
                                        </a>
                                    </Link>
                                    <div className="w-100 py-2 ps-2 mb-4 mx-2"></div>
                                </div>
                            </>
                        )}

                    </div>
                </div>
            )}
        </div>
    )
}
