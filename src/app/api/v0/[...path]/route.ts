import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'

async function proxyRequest(request: NextRequest, { params }: RouteContext<'/api/v0/[...path]'>) {
  const { path } = await params

  let headers = Array.from(request.headers.entries()).filter(
    ([key]) => (key.startsWith('x-') && !key.startsWith('x-forwarded')) || ['origin', 'referer', 'user-agent'].includes(key)
  )
  headers.push(['content-type', request.headers.get('content-type') ?? 'application/json'])

  const cookieStore = await cookies()
  const session = cookieStore.get('session_id')?.value

  if (session !== undefined && !request.headers.has('x-session'))
    headers.push(['x-session', session])

  const isMutationRequest = ['POST', 'PUT', 'PATCH'].includes(request.method)

  if (isMutationRequest && !request.headers.has('x-csrftoken')) {
    const csrfHeaders = [] as [string, string][]
    if (session !== undefined)
      csrfHeaders.push(['x-session', session])

    const response = await fetch(`${process.env.API_SERVER}/api/v0/csrf/`, {
      headers: csrfHeaders,
      credentials: 'include' 
    })
    if (!response.ok)
      throw new Error(await response.text())
    const data = await response.json()
    if (data.csrf)
      headers.push(['x-csrftoken', data.csrf])
    // TODO: should we also set cookie here?
  }

  const url = new URL(`${process.env.API_SERVER}/api/v0/${path.join('/')}/`)
  url.search = request.nextUrl.searchParams.toString()

  try {
    const response = await fetch(url, {
      method: request.method,
      headers,
      body: isMutationRequest ? await request.bytes() : null,
      credentials: 'include',
      redirect: 'manual',
    })

    headers = Array.from(response.headers.entries()).filter(
      ([key]) => key.startsWith('content-') || key.startsWith('x-')
    )

    const setCookieHeaders = response.headers.getSetCookie();
    setCookieHeaders.forEach(cookie => headers.push(['set-cookie', cookie]))

    cookieStore.set('session_id', response.headers.get('x-session') ?? '', {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict',
    })

    return new NextResponse(response.body, {
      status: response.status,
      headers,
    })
  } catch (error) {
    console.log(url.toString())
    console.log(error)
    return NextResponse.json({ error: 'Proxy fetch failed' }, { status: 500 });
  }
}

export {
  proxyRequest as GET,
  proxyRequest as POST,
  proxyRequest as PUT,
}
