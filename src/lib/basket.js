import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { useQuery, useMutation, useQueryClient } from 'react-query';

import { withSession, basketKeys, loadBasket, createBasket, addBasketItem, removeBasketItem, updateBasketItem } from '@/lib/queries';

export default function useBasket() {
    const [basket, setBasket] = useState({});
    const [isEmpty, setEmpty] = useState(true);
    const {data: session} = useSession();

    const queryClient = useQueryClient();

    const { data: baskets, isSuccess, isLoading, isError } = useQuery(
        basketKeys.detail(),
        () => withSession(session, loadBasket),
        {
            onError: (error) => {
                console.log(error);
            }
        }
    );

    useEffect(() => {
        const empty = baskets === undefined || baskets.length === 0 || baskets[0].items.length === 0;
        setEmpty(empty);
        setBasket(empty ? {} : baskets[0]);
    }, [baskets]);

    const createBasketMutation = useMutation(() => withSession(session, createBasket));
    const addBasketItemMutation = useMutation(({basketId, productId}) => withSession(session, addBasketItem, basketId, productId, 1), {
        onSuccess: () => {
            queryClient.invalidateQueries(basketKeys.all);
        }
    });
    const removeBasketItemMutation = useMutation(({basketId, productId}) => withSession(session, removeBasketItem, basketId, productId), {
        onSuccess: () => {
            queryClient.invalidateQueries(basketKeys.all);
        }
    });
    const updateBasketItemMutation = useMutation(({basketId, productId, quantity}) => withSession(session, updateBasketItem, basketId, productId, quantity), {
        onSuccess: () => {
            queryClient.invalidateQueries(basketKeys.all);
        }
    });

    const addItem = (productId) => {
        if (baskets.length === 0) {
            createBasketMutation.mutate(undefined, {
                onSuccess: (data) => {
                    console.log(data);
                    addBasketItemMutation.mutate({basketId: data.id, productId});
                }
            });
        } else {
            addBasketItemMutation.mutate({basketId: baskets[0].id, productId});
        }
    };

    const removeItem = (productId) => {
        removeBasketItemMutation.mutate({basketId: baskets[0].id, productId});
    };

    const setQuantity = (productId, quantity) => {
        updateBasketItemMutation.mutate({basketId: baskets[0].id, productId, quantity});
    };

    return { basket, addItem, removeItem, setQuantity, isEmpty, isSuccess, isLoading, isError };
}
