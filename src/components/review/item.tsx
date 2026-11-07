import ReviewRating from '@/components/review/rating'
import UserAvatar from '@/components/user/avatar'

import { ProductReview } from '@/lib/types'

import moment from 'moment'

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export default function ReviewItem({ review, first, last }: { review: ProductReview, first?: boolean, last?: boolean }) {
  return (
    <div className={`mb-6 pb-6 ${last ? '' : 'border-b'}`} id={"r" + review.id}>
      <div className="mb-4 flex">
        <div className="me-6 flex items-center pe-2">
          <UserAvatar gravatar={review.user.gravatar} name={review.user.full_name} size={50} border />
          <div className="ps-4">
            <h6 className="mb-0 text-sm leading-[1.2] font-medium">{review.user.full_name}</h6>
            <span className="hidden text-ms text-muted">{moment(review.submit_date).fromNow()}</span>
          </div>
        </div>
        <div>
          <div><ReviewRating value={review.rating.value} /></div>
          <div className="text-ms text-muted">
            {review.rating.text}
            {(review.weight > 1 && review.weight <= 10) ? (
              <> &mdash; отзыв покупателя</>
            ) : review.weight > 10 && (
              <> &mdash; отзыв эксперта</>
            )}
          </div>
        </div>
      </div>
      <p className="mb-2 text-md whitespace-pre-line">{review.comment}</p>
    </div>
  )
}
