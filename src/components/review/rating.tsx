import { IconStar, IconStarFilled, IconStarHalfFilled } from '@tabler/icons-react'

const sizes = {
  xs: { size: 12, className: 'me-[.1875rem]' },
  sm: { size: 14, className: 'me-1' },
}

function Star({ star, value, size }: { star: number, value: number, size: keyof typeof sizes }) {
  const Icon = star <= value ? IconStarFilled : star <= value + 0.7 ? IconStarHalfFilled : IconStar
  return <Icon size={sizes[size].size} stroke={1.5} className={`align-middle ${sizes[size].className}`} />
}

// Five stars in the warning color, filled up to the value
export default function ReviewRating({ value, size = 'xs' }: { value: number, size?: keyof typeof sizes }) {
  return (
    <div className="inline-block leading-none whitespace-nowrap text-warning" role="img" aria-label={`Оценка ${value.toFixed(1)} из 5`}>
      {[1, 2, 3, 4, 5].map(star => <Star star={star} value={value} size={size} key={star} />)}
    </div>
  )
}
