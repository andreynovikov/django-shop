import React, { useState, useEffect, useRef } from 'react';
import { useSession } from 'next-auth/react';
import { useQuery } from 'react-query';

import { withSession, productKeys, getProductPrice } from '@/lib/queries';

export default function ProductPrice({product}) {
    const [cost, setCost] = useState(product.cost);
    const { data: session, status } = useSession();

    const { data: userPrice } = useQuery(
        productKeys.price(product.id),
        () => withSession(session, getProductPrice, product.id),
        {
            enabled: status === 'authenticated',
            onError: (error) => {
                console.log(error);
            }
        }
    );

    useEffect(() => {
        setCost(userPrice ? userPrice.cost : product.cost);
    }, [userPrice]);

    if (product.enabled && cost > 0)
        return (
            <>
	            { cost.toLocaleString('ru') }<small>&nbsp;руб</small>
                { cost != product.price && <>{' '}<del className="fs-sm text-muted">{ product.price.toLocaleString('ru') }<small>&nbsp;руб</small></del></> }
            </>
        )
    else
        return <small>товар снят с продажи</small>
}

