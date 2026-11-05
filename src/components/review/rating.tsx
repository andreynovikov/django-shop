import { IconStar, IconStarFilled, IconStarHalfFilled } from '@tabler/icons-react'

function getStarIcon(star: number, value: number) {
  if (star <= value)
    return <IconStarFilled />
  else if (star <= (value + 0.7))
    return <IconStarHalfFilled />
  else
    return <IconStar />
}

export default function ReviewRating({ value }: { value: number }) {
  return (
    <ul className="me-2 flex">
      <li>{getStarIcon(1, value)}</li>
      <li>{getStarIcon(2, value)}</li>
      <li>{getStarIcon(3, value)}</li>
      <li>{getStarIcon(4, value)}</li>
      <li>{getStarIcon(5, value)}</li>
    </ul>
  )
}
