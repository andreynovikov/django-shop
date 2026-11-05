import { SVGProps } from 'react'

import SvgIcon from '@/components/svg-icon'

type NoImageProps = SVGProps<SVGSVGElement> & {
  size?: number,
  block?: boolean
}

// The props of cartzilla's NoImage, drawn with familysew's orion box icon
export default function NoImage({ size = 200, block = false, className, style, ...props }: NoImageProps) {
  const sizeStyle = block ? {
    width: size,
    height: size
  } : {
    width: size,
    height: size,
    padding: Math.floor(size / 4)
  }

  return (
    <SvgIcon
      id="shipping-box-1"
      className={"svg-icon text-muted " + (block ? "mx-auto block" : "inline-block") + (className ? " " + className : "")}
      style={{ ...sizeStyle, ...style }}
      {...props} />
  )
}
