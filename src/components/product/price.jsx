import React, { useState, useEffect } from 'react';
import { useQuery } from 'react-query';

import { useSession } from '@/lib/session';
import { productKeys, getProductPrice } from '@/lib/queries';

export default function ProductPrice({product, delFs, ...props}) {
    const [cost, setCost] = useState(product.cost);
    const { status } = useSession();

    const { data: userPrice } = useQuery(
        productKeys.price(product.id),
        () => getProductPrice(product.id),
        {
            enabled: status === 'authenticated',
            onError: (error) => {
                console.log(error);
            }
        }
    );

    useEffect(() => {
        setCost(userPrice ? userPrice.cost : product.cost);
    }, [userPrice, product.cost]);

    if (product.enabled && cost > 0)
        return (
            <>
	            <span {...props}>{ cost.toLocaleString('ru') }<small>&nbsp;руб</small></span>
                { cost != product.price && (
                    <>
                        {" "}
                        <del className={`fs-${delFs ? delFs : "sm"} text-muted`}>
                            { product.price.toLocaleString('ru') }
                            <small>&nbsp;руб</small>
                        </del>
                    </>
                )}
            </>
        )
    else
        return <small>товар снят с продажи</small>
}

