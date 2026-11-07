import { IconCamera } from '@tabler/icons-react'

// A camera in place of a missing product picture, in a square of `size` or, as a `block`, centered
export default function NoImage({ size = 200, block = false }: { size?: number, block?: boolean }) {
  if (block)
    return <IconCamera size={size} stroke={1} className="mx-auto block text-muted" />

  return (
    <span className="inline-block text-muted" style={{ width: size, height: size, padding: Math.floor(size / 4) }}>
      <IconCamera size={Math.floor(size / 2)} stroke={1} className="block" />
    </span>
  )
}
