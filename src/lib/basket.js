import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import { basketKeys, loadBasket, createBasket, addBasketItem, removeBasketItem, updateBasketItem } from '@/lib/queries';

export default function useBasket() {
    const queryClient = useQueryClient();

    const { data: baskets, isSuccess, isLoading, isError } = useQuery({
        queryKey: basketKeys.details(),
        queryFn: () => loadBasket()
    });

    const isEmpty = baskets === undefined || baskets.length === 0 || baskets[0].items.length === 0;
    const basket = isEmpty ? {} : baskets[0];

    const createBasketMutation = useMutation({
        mutationFn: () => createBasket()
    });
    const addBasketItemMutation = useMutation({
        mutationFn: ({basketId, productId, quantity}) => addBasketItem(basketId, productId, quantity),
        onSuccess: () => {
            queryClient.invalidateQueries({queryKey: basketKeys.all});
        }
    });
    const removeBasketItemMutation = useMutation({
        mutationFn: ({basketId, productId}) => removeBasketItem(basketId, productId),
        onSuccess: () => {
            queryClient.invalidateQueries({queryKey: basketKeys.all});
        }
    });
    const updateBasketItemMutation = useMutation({
        mutationFn: ({basketId, productId, quantity}) => updateBasketItem(basketId, productId, quantity),
        onSuccess: () => {
            queryClient.invalidateQueries({queryKey: basketKeys.all});
        }
    });

    const addItem = (productId, quantity = 1) => {
        if (baskets.length === 0) {
            createBasketMutation.mutate(undefined, {
                onSuccess: (data) => {
                    console.log(data);
                    addBasketItemMutation.mutate({basketId: data.id, productId, quantity});
                }
            });
        } else {
            addBasketItemMutation.mutate({basketId: baskets[0].id, productId, quantity});
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
