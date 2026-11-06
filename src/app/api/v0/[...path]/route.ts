import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'

async function proxyRequest(request: NextRequest, { params }: RouteContext<'/api/v0/[...path]'>) {
  const { path } = await params

  const isMutationRequest = ['POST', 'PUT', 'PATCH'].includes(request.method)

  let headers = Array.from(request.headers.entries()).filter(
    ([key]) => (key.startsWith('x-') && !key.startsWith('x-forwarded')) || ['origin', 'referer', 'cookie', 'user-agent'].includes(key)
  )
  headers.push(['content-type', request.headers.get('content-type') ?? 'application/json'])

  // POST requests in Django require header (not cookie)
  if (isMutationRequest && !request.headers.has('x-csrftoken')) {
    const cookieStore = await cookies()
    const csrf = cookieStore.get('csrftoken')?.value
    if (csrf !== undefined)
      headers.push(['x-csrftoken', csrf])
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

    // Pass cookies to browser
    const setCookieHeaders = response.headers.getSetCookie();
    setCookieHeaders.forEach(cookie => headers.push(['set-cookie', cookie]))

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
