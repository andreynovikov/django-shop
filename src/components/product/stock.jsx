import { useState, useMemo } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';

import Button from 'react-bootstrap/Button';
import Collapse from 'react-bootstrap/Collapse';

import SimpleBar from 'simplebar-react';

import Loading from '@/components/loading';

import { productKeys, loadProductStock } from '@/lib/queries';

function Collapsable({title, children}) {
    const [open, setOpen] = useState(false);

    return (
        <>
            <Button variant="link" className="d-block p-0 fs-sm product-meta" onClick={() => setOpen(!open)}>
                { title }
            </Button>
            <Collapse in={open}>
                <div>
                    { children }
                </div>
            </Collapse>
        </>
    )
}

export default function ProductStock({ id }) {
    const { data: stores, isSuccess, isLoading } = useQuery({
        queryKey: productKeys.stock(id),
        queryFn: () => loadProductStock(id),
        enabled: id > 0
    });

    const storeGroups = useMemo(() => {
        if (!isSuccess)
            return [];

        const { groups } = stores.reduce(({ groups, city }, store) => {
            if (store.city.id !== city) {
                groups.push({city: store.city, stores: []});
                city = store.city.id;
            }
            groups[groups.length - 1].stores.push(store);
            return { groups, city };
        }, {groups: [], city: null});

        return groups.sort((a, b) => a.city.name.localeCompare(b.city.name));
    }, [stores, isSuccess]);

    if (isLoading)
        return <Loading className="text-center" />

    if (!isSuccess || stores.length === 0)
        return <div className="fw-bold text-dark py-3">Данного товара нет в наличии в розничных магазинах</div>

    return (
        <SimpleBar style={{maxHeight: "14rem"}} autoHide={false}>
            <div className="pt-2 pb-3 fs-sm">Товар есть в наличии в следующих магазинах:</div>
            { storeGroups.map(({ city, stores }, index) => (
                <div className={"border-bottom " + (index === 0 ? "pb-2" : "py-2")} key={city.id}>
                    <Collapsable title={ city.name }>
                        { stores.map((store) => (
                            <Link className="d-block fs-xs pt-1" href={{ pathname: '/stores/[id]', query: { id: store.id } }} key={store.id}>
                                <i className="ci-check me-1 text-muted" />
                                { store.address }
                            </Link>
                        ))}
                    </Collapsable>
                </div>
            ))}
            <div className="pt-2 fs-xs text-muted">
                Наличие в других магазинах сети можно уточнить по <Link href="/stores">телефонам магазинов</Link>
            </div>
        </SimpleBar>
    )
}
