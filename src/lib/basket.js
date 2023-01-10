import { useQuery, useMutation, useQueryClient } from 'react-query';

import { toast } from 'react-toastify';

import { basketKeys, loadBasket, createBasket, addBasketItem, removeBasketItem, updateBasketItem } from '@/lib/queries';

export default function useBasket() {
    const queryClient = useQueryClient();

    const { data: baskets, isSuccess, isLoading, isError } = useQuery(
        basketKeys.details(),
        () => loadBasket(),
        {
            placeholderData: [],
            onError: (error) => {
                console.log(error);
            }
        }
    );

    const isEmpty = baskets.length === 0 || baskets[0].items.length === 0;
    const basket = isEmpty ? {} : baskets[0];

    const createBasketMutation = useMutation(() => createBasket());
    const addBasketItemMutation = useMutation(({basketId, productId, quantity}) => addBasketItem(basketId, productId, quantity), {
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

    const addItem = (productId, quantity = 1) => {
        if (baskets.length === 0) {
            createBasketMutation.mutate(undefined, {
                onSuccess: (data) => {
                    addBasketItemMutation.mutate({basketId: data.id, productId, quantity});
                }
            });
        } else {
            addBasketItemMutation.mutate({basketId: baskets[0].id, productId, quantity});
        }
        toast("Товар добавлен в корзину");
    };

    const removeItem = (productId) => {
        removeBasketItemMutation.mutate({basketId: baskets[0].id, productId});
    };

    const setQuantity = (productId, quantity) => {
        updateBasketItemMutation.mutate({basketId: baskets[0].id, productId, quantity});
    };

    return { basket, addItem, removeItem, setQuantity, isEmpty, isSuccess, isLoading, isError };
}
