import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { useQuery, useMutation, useQueryClient } from 'react-query';

import { withSession, favoriteKeys, loadFavorites, addToFavorites, removeFromFavorites } from '@/lib/queries';

export default function useFavorites() {
    const {data: session, status} = useSession();

    const queryClient = useQueryClient();

    const { data: favorites, isSuccess, isLoading, isError } = useQuery(
        favoriteKeys.detail(),
        () => withSession(session, loadFavorites),
        {
            enabled: status === 'authenticated',
            initialData: [],
            onError: (error) => {
                console.log(error);
            }
        }
    );

    const addToFavoritesMutation = useMutation((productId) => withSession(session, addToFavorites, productId), {
        onSuccess: () => {
            queryClient.invalidateQueries(favoriteKeys.all);
        }
    });
    const removeFromFavoritesMutation = useMutation((productId) => withSession(session, removeFromFavorites, productId), {
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
