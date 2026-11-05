import { IconCamera } from '@tabler/icons-react'

export default function NoImage({ size = 200, block = false, className = '' }: { size?: number, block?: boolean, className?: string }) {
  const style = block ? {
    width: size,
    height: size,
  } : {
    width: size,
    height: size,
    padding: Math.floor(size / 4)
  }

  return (
    <IconCamera className={(block ? "mx-auto block" : "inline-block") + " text-muted " + className} style={style} stroke={1.5} />
  )
}
