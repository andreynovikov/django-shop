import { useState, useEffect } from 'react';

import ReviewRating from '@/components/review/rating';
import UserAvatar from '@/components/user/avatar';

import axios from 'axios';
import moment from 'moment';
import 'moment/locale/ru';

moment.locale('ru');

export default function ReviewItem({review, first, last}) {

    return (
        <div className={"product-review mb-4 pb-4" + (!last && " border-bottom")} id={"r" + review.id }>
            <div className="d-flex mb-3">
                <div className="d-flex align-items-center me-4 pe-2">
                    <UserAvatar gravatar={review.user.gravatar} name={ review.user.full_name } size="50" border />
                    <div className="ps-3">
                        <h6 className="fs-sm mb-0">{ review.user.full_name }</h6>
                        <span className="fs-ms text-muted">{ moment(review.submit_date).fromNow() }</span>
                    </div>
                </div>
                <div>
                    <div className="star-rating"><ReviewRating value={ review.rating.value } /></div>
                    <div className="fs-ms text-muted">
                        { review.rating.text }
                        { (review.weight > 1 && review.weight <= 10) ? (
                            <> &mdash; отзыв покупателя</>
                        ) : review.weight > 10 && (
                            <> &mdash; отзыв эксперта</>
                        )}
                    </div>
                </div>
            </div>
            <p className="fs-md mb-2" style={{whiteSpace: "pre-line"}}>{ review.comment }</p>
        </div>
    )
}
