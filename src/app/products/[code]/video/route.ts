import { NextRequest } from 'next/server'
import { redirect } from 'next/navigation'

export async function GET(request: NextRequest, { params }: RouteContext<'/products/[code]/video'>) {
  const { code } = await params
  redirect(`https://api.sewing-world.ru/api/v0/products/${code}/video/`)
}