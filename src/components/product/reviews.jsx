import { useState, useEffect, useRef } from 'react';
import { useQuery } from 'react-query';

import ReviewRating from '@/components/review/rating';
import ReviewItem from '@/components/review/item';
import ReviewForm from '@/components/review/form';
import SignInModal from '@/components/sign-in-modal';

import rupluralize from '@/lib/rupluralize';
import { useSession } from '@/lib/session';
import { reviewKeys, loadProductReviews } from '@/lib/queries';

const colors = ['#42d697', '#a7e453', '#ffda75', '#fea569', '#f34770'];

export default function ProductReviews({product}) {
    const modalRef = useRef();
    const [ratingChoices, setRatingChoices] = useState([]);

    const { status } = useSession();

    const { data: reviews, isSuccess } = useQuery(
        reviewKeys.list(product.id),
        () => loadProductReviews(product.id)
    );

    useEffect(() => {
        if (isSuccess && reviews.count > 0) {
            const choices = [];
            var rating = 0;
            for (var r = 1; r < 6; r++) {
                if (rating === reviews.statistics.ratings.length || reviews.statistics.ratings[rating].rating > r) {
                    choices.push({
                        'rating': r,
                        'count': 0,
                        'percent': 0
                    });
                    continue;
                }
                choices.push({
                    ...reviews.statistics.ratings[rating],
                    percent: Math.ceil(reviews.statistics.ratings[rating].count / reviews.count * 100)
                });
                rating++;
            }
            setRatingChoices(choices);
        }
    }, [isSuccess, reviews]);

    if (!isSuccess)
        return (
            <div>Loading...</div>
        )

    return (
        <>
            { reviews.count > 0 && (
                <>
                    <div className="row pb-3">
                        <div className="col-lg-4 col-md-5">
                            <h2 className="h3 mb-4">{ reviews.count } { rupluralize(reviews.count, ['обзор', 'обзора', 'обзоров']) }</h2>
                            <ReviewRating value={reviews.statistics.value} classAddon="text-accent fs-sm me-1" />
                            <span className="d-inline-block align-middle ms-1">{ reviews.statistics.value.toFixed(1) } &ndash; { reviews.statistics.text }</span>
                        </div>
                        <div className="col-lg-8 col-md-7">
                            { ratingChoices.map((choice, index) => (
                                <div className="d-flex align-items-center mb-2" key={index}>
                                    <div className="text-nowrap me-3">
                                        <span className="d-inline-block align-middle text-muted">{ choice.rating }</span>
                                        <i className="ci-star-filled fs-xs ms-1" />
                                    </div>
                                    <div className="w-100">
                                        <div className="progress" style={{height: "4px"}}>
                                            <div
                                                className="progress-bar"
                                                role="progressbar"
                                                style={{width: choice.percent + "%", backgroundColor: colors[index]}}
                                                aria-valuenow={ choice.percent }
                                                aria-valuemin="0"
                                                aria-valuemax="100">
                                            </div>
                                        </div>
                                    </div>
                                    <span className="text-muted ms-3">{ choice.count }</span>
                                </div>
                            ))}
                        </div>
                    </div>
                    <hr className="mt-4 mb-3" />
                </>
            )}
            <div className="row pt-4">
                <div className="col-md-7">
                    { reviews.results.length > 0 ? (
                        reviews.results.map((review, index) => <ReviewItem review={review} last={index === reviews.results.length - 1} key={review.id} />)
                    ) : (
                        <div>Нет отзывов об этом товаре. Вы можете быть первым, кто опубликует отзыв.</div>
                    )}
                </div>
                <div className="col-md-5 mt-2 pt-4 mt-md-0 pt-md-0">
                    <div className="bg-secondary py-grid-gutter px-grid-gutter rounded-3">
                        { status === 'authenticated' ? (
                            <ReviewForm product={product} review={reviews.user_reviews?.[0]} />
                        ) : (
                            <div>
                                <SignInModal ref={modalRef} ctx="reviews" />
                                Отзывы о товаре могут оставлять только{" "}
                                <a onClick={() => modalRef.current.showModal()}>зарегистрированные</a>
                                {" "}покупатели.
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </>
    )
}
