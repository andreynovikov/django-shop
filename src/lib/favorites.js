import { useQuery, useMutation, useQueryClient } from 'react-query';

import { useSession } from '@/lib/session';
import { favoriteKeys, loadFavorites, addToFavorites, removeFromFavorites } from '@/lib/queries';

export default function useFavorites() {
    const { status } = useSession();

    const queryClient = useQueryClient();

    const { data: favorites, isSuccess, isLoading, isError } = useQuery(
        favoriteKeys.details(),
        () => loadFavorites(),
        {
            enabled: status === 'authenticated',
            initialData: [],
            onError: (error) => {
                console.log(error);
            }
        }
    );

    const addToFavoritesMutation = useMutation((productId) => addToFavorites(productId), {
        onSuccess: () => {
            queryClient.invalidateQueries(favoriteKeys.all);
        }
    });
    const removeFromFavoritesMutation = useMutation((productId) => removeFromFavorites(productId), {
        onSuccess: () => {
            queryClient.invalidateQueries(favoriteKeys.all);
        }
    });

    const favoritize = (productId) => {
        addToFavoritesMutation.mutate(productId);
    };

    const unfavoritize = (productId) => {
        removeFromFavoritesMutation.mutate(productId);
    };

    return { favorites, favoritize, unfavoritize, isSuccess, isLoading, isError };
}
