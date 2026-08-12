import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'

async function proxyRequest(request: NextRequest, { params }: RouteContext<'/api/v0/[...path]'>) {
  const { path } = await params
  const url = new URL(`${process.env.API_SERVER}/api/v0/${path.join('/')}/`)
  url.search = request.nextUrl.searchParams.toString()

  let headers = Array.from(request.headers.entries()).filter(
    ([key]) => key.startsWith('x-') || ['origin', 'referer', 'user-agent'].includes(key)
  )
  headers.push(['content-type', request.headers.get('content-type') ?? 'application/json'])

  try {
    const response = await fetch(url, {
      method: request.method,
      headers,
      body: ['POST', 'PUT', 'PATCH'].includes(request.method) ? await request.bytes() : null,
      credentials: 'include',
      redirect: 'manual',
    })

    headers = Array.from(response.headers.entries()).filter(
      ([key]) => key.startsWith('content-') || key.startsWith('x-')
    )

    const cookieStore = await cookies()

    cookieStore.set('session_id', response.headers.get('x-session') ?? '', {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict',
      path: '/',
    })

    return new NextResponse(response.body, {
      status: response.status,
      headers,
    })
  } catch (error) {
    console.log(error)
    return NextResponse.json({ error: 'Proxy fetch failed' }, { status: 500 });
  }
}

export {
  proxyRequest as GET,
  proxyRequest as POST,
  proxyRequest as PUT,
}
