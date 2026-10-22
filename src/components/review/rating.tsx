function getStarClassName(star: number, value: number, classAddon?: string) {
  let modifier = ''
  if (star <= value)
    modifier = '-filled'
  else if (star <= (value + 0.7))
    modifier = '-half'
  return `ci-star${modifier} active ${classAddon ? classAddon : "star-rating-icon"}`
}

export default function ReviewRating({ value, classAddon }: { value: number, classAddon?: string }) {
  return (
    <div className="star-rating">
      <i className={getStarClassName(1, value, classAddon)} />
      <i className={getStarClassName(2, value, classAddon)} />
      <i className={getStarClassName(3, value, classAddon)} />
      <i className={getStarClassName(4, value, classAddon)} />
      <i className={getStarClassName(5, value, classAddon)} />
    </div>
  )
}
