import { useQuery } from 'react-query';

import ReviewRating from '@/components/review/rating';

import rupluralize from '@/lib/rupluralize';
import { reviewKeys, getProductRating } from '@/lib/queries';

export default function ProductRating({product}) {
    const { data: average, isSuccess } = useQuery(
        reviewKeys.rating(product),
        () => getProductRating(product)
    );

    if (!isSuccess || average.count === 0)
        return null;

    return (
        <>
            <ReviewRating value={ average.value } />
            <span class="text-muted text-uppercase text-sm">
                { average.count } { rupluralize(average.count, ['обзор', 'обзора', 'обзоров']) }
            </span>
        </>
    )
}
