import { useQuery, useMutation, useQueryClient } from 'react-query';

import { basketKeys, loadBasket, createBasket, addBasketItem, removeBasketItem, updateBasketItem } from '@/lib/queries';

export default function useBasket() {
    const queryClient = useQueryClient();

    const { data: baskets, isSuccess, isLoading, isError } = useQuery(
        basketKeys.details(),
        () => loadBasket(),
        {
            onError: (error) => {
                console.log(error);
            }
        }
    );

    const isEmpty = baskets === undefined || baskets.length === 0 || baskets[0].items.length === 0;
    const basket = isEmpty ? {} : baskets[0];

    const createBasketMutation = useMutation(() => createBasket());
    const addBasketItemMutation = useMutation(({basketId, productId}) => addBasketItem(basketId, productId, 1), {
        onSuccess: () => {
            queryClient.invalidateQueries(basketKeys.all);
        }
    });
    const removeBasketItemMutation = useMutation(({basketId, productId}) => removeBasketItem(basketId, productId), {
        onSuccess: () => {
            queryClient.invalidateQueries(basketKeys.all);
        }
    });
    const updateBasketItemMutation = useMutation(({basketId, productId, quantity}) => updateBasketItem(basketId, productId, quantity), {
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
