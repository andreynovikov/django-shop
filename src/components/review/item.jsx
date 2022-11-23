import ReviewRating from '@/components/review/rating';
import UserAvatar from '@/components/user/avatar';

import moment from 'moment';
import 'moment/locale/ru';

moment.locale('ru');

export default function ReviewItem({review, first, last}) {

    return (
        <div className="review d-flex" id={"r" + review.id }>
            <div className="flex-shrink-0 text-center me-4 me-xl-5">
                <UserAvatar className="review-image" gravatar={review.user.gravatar} name={ review.user.full_name } size="120" />
                <span className="text-uppercase text-muted">{ moment(review.submit_date).fromNow() }</span>
            </div>
            <div>
                <h5 className="mt-2 mb-1">{ review.user.full_name }</h5>
                <div className="mb-2 text-warning text-sm">
                    <ReviewRating value={ review.rating.value } />
                </div>
                <p className="text-muted" style={{whiteSpace: "pre-line"}}>{ review.comment }</p>
            </div>
        </div>
    )
}
