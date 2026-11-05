import ReviewRating from '@/components/review/rating'
import UserAvatar from '@/components/user/avatar'

import { ProductReview } from '@/lib/types'

import moment from 'moment'

const avatarClass = 'mx-auto mb-2 block w-25 max-w-full rounded-full border bg-white p-1.5 md:w-30 md:p-2'
const labelClass = 'text-xs tracking-widest uppercase'
const textClass = 'mb-4 whitespace-pre-line text-muted'

export default function ReviewItem({ review }: { review: ProductReview, last?: boolean }) {
  return (
    <div className="flex border-b border-gray-200 px-4 py-8 first-of-type:pt-4 last-of-type:border-b-0" id={"r" + review.id}>
      <div className="me-6 shrink-0 text-center xl:me-12">
        {review.reviewer_name ? (
          <UserAvatar className={avatarClass} gravatar={review.reviewer_avatar} name={review.reviewer_name} size={120} />
        ) : (
          <UserAvatar className={avatarClass} gravatar={review.user.gravatar} name={review.user.full_name} size={120} />
        )}
        {/* relative to the time of rendering, the static page is older than the browser's clock */}
        <span className="tracking-widest text-muted uppercase" suppressHydrationWarning>{moment(review.submit_date).fromNow()}</span>
      </div>
      <div>
        <h5 className="mt-2 mb-1 text-lg leading-[1.1] font-bold">{review.reviewer_name ? review.reviewer_name : review.user.full_name}</h5>
        <div className="mb-2 text-xs text-warning">
          <ReviewRating value={review.rating.value} />
        </div>
        {review.advantage && (
          <>
            <div className={labelClass}>Достоинства</div>
            <p className={textClass}>{review.advantage}</p>
          </>
        )}
        {review.disadvantage && (
          <>
            <div className={labelClass}>Недостатки</div>
            <p className={textClass}>{review.disadvantage}</p>
          </>
        )}
        {review.comment && (
          <>
            {(review.advantage || review.disadvantage) && (
              <div className={labelClass}>Комментарий</div>
            )}
            <p className={textClass}>{review.comment}</p>
          </>
        )}
      </div>
    </div>
  )
}
