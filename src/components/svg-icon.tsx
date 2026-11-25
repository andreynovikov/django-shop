import { SVGProps } from 'react'

export const spritePath = '/vendor/sell/orion-svg-sprite.svg'

// An icon of the Orion sprite that came with the old "Sell" theme, by its id in the sprite
export default function SvgIcon({ id, ...props }: SVGProps<SVGSVGElement> & { id: string }) {
  return (
    <svg {...props}>
      <use href={`${spritePath}#${id}`} />
    </svg>
  )
}
