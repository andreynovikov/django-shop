import { useRouter } from 'next/router';
import Link from 'next/link';
import { useQuery } from 'react-query';

import ReviewItem from '@/components/review/item';
import ReviewForm from '@/components/review/form';

import { useSession } from '@/lib/session';
import { reviewKeys, loadProductReviews } from '@/lib/queries';

export default function ProductReviews({product}) {
    const router = useRouter();

    const { status } = useSession();

    const { data: reviews, isSuccess } = useQuery(
        reviewKeys.list(product.id),
        () => loadProductReviews(product.id)
    );

    if (!isSuccess)
        return (
            <div>Loading...</div>
        )

    return (
        <div className="row mb-5">
            <div className="col-lg-10 col-xl-9">
                { reviews.results.length > 0 ? (
                    reviews.results.map((review, index) => <ReviewItem review={review} last={index === reviews.results.length - 1} key={review.id} />)
                ) : (
                    <div>Нет отзывов об этом товаре. Вы можете быть первым, кто опубликует отзыв.</div>
                )}
                <div className="py-5 px-3">
                    { status === 'authenticated' ? (
                        <ReviewForm product={product} review={reviews.user_reviews?.[0]} />
                    ) : (
                        <div>
                            Отзывы о товаре могут оставлять только{" "}
                            <Link href={{ pathname:"/login", query: { callbackUrl: router.asPath }}}>
                                зарегистрированные
                            </Link>
                            {" "}пользователи.
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
