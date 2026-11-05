import { SVGProps } from 'react'

export const spritePath = '/vendor/sell/orion-svg-sprite.svg'

export default function SvgIcon({ id, ...props }: SVGProps<SVGSVGElement> & { id: string }) {
  return (
    <svg {...props}>
      <use href={`${spritePath}#${id}`} />
    </svg>
  )
}
