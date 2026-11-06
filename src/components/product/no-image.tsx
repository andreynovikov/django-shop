import { HTMLAttributes } from 'react'

// Dor Tak's placeholder with the props of cartzilla's NoImage, which is a Cartzilla font icon
export default function NoImage({ size = 160, block = false, ...props }: { size?: number, block?: boolean } & HTMLAttributes<HTMLSpanElement>) {
  const style = {
    width: size,
    height: size,
    padding: Math.floor(size / 4)
  }

  return (
    <span className={(block ? "d-block mx-auto" : "d-inline-block") + " text-muted"} style={style} {...props}>&#8709;</span>
  )
}
