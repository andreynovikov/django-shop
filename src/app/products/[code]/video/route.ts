import { NextRequest } from 'next/server'
import { redirect } from 'next/navigation'

import { loadProductByCode } from '@/lib/queries'
import { Product } from '@/lib/types'

export async function GET(request: NextRequest, { params }: RouteContext<'/products/[code]/video'>) {
  const { code } = await params
  const product = (await loadProductByCode(code)) as Product
  if (!product.video_url)
    return Response.json({ error: 'Video does not exist' }, { status: 404 })
  redirect(`https://api.sewing-world.ru/api/v0/products/${code}/video/`)
}