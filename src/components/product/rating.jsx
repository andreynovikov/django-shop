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
        <div>
            <ReviewRating value={ average.value } />
            <span className="d-inline-block fs-sm text-white opacity-70 align-middle mt-1 ms-1">
                { average.count } { rupluralize(average.count, ['обзор', 'обзора', 'обзоров']) }
            </span>
        </div>
    )
}
