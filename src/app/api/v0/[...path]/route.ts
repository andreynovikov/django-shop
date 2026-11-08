import { NextRequest, NextResponse } from 'next/server'

// Only these reach the backend, so client-supplied X-Session, X-Real-IP and the like stay here
const REQUEST_HEADERS = ['cookie', 'origin', 'referer', 'user-agent', 'content-type']
const RESPONSE_HEADERS = ['cache-control', 'vary', 'retry-after']

// The old name is read until the backend's cookie rename has been out for SESSION_COOKIE_AGE (4 weeks)
const CSRF_COOKIES = ['__Host-csrftoken', 'csrftoken']

async function proxyRequest(request: NextRequest, { params }: RouteContext<'/api/v0/[...path]'>) {
  const { path } = await params

  const isMutationRequest = ['POST', 'PUT', 'PATCH'].includes(request.method)

  // Pages on other origins can't send a custom header: no-cors drops it, and cors needs a preflight
  // this route never approves. Sec-Fetch-Site is set by the browser and also catches same-site subdomains.
  if (isMutationRequest) {
    const fetchSite = request.headers.get('sec-fetch-site')
    if (!request.headers.has('x-requested-with') || (fetchSite !== null && fetchSite !== 'same-origin'))
      return NextResponse.json({ error: 'Cross-site request' }, { status: 403 })
  }

  // Next decodes each segment, so an encoded dot segment or slash would change the path upstream
  if (path.some(segment => segment === '.' || segment === '..' || /[/\\]/.test(segment)))
    return NextResponse.json({ error: 'Invalid path' }, { status: 400 })
  const endpoint = path.join('/')

  // Logout is a POST, so that other pages can't sign the visitor out with a link or an image
  if (request.method === 'GET' && endpoint === 'users/logout')
    return NextResponse.json({ error: 'Method not allowed' }, { status: 405, headers: { allow: 'POST' } })

  const headers = REQUEST_HEADERS.flatMap(key => {
    const value = request.headers.get(key)
    return value === null ? [] : [[key, value] as [string, string]]
  })

  // Django checks the header against the cookie for signed-in users. The checks above are what keep
  // other sites out; the copy only satisfies Django.
  if (isMutationRequest) {
    const csrf = CSRF_COOKIES.map(name => request.cookies.get(name)?.value).find(value => value !== undefined)
    if (csrf !== undefined)
      headers.push(['x-csrftoken', csrf])
  }

  const url = new URL(`${process.env.API_SERVER}/api/v0/${path.map(encodeURIComponent).join('/')}/`)
  url.search = request.nextUrl.searchParams.toString()
  if (!url.pathname.startsWith('/api/v0/'))
    return NextResponse.json({ error: 'Invalid path' }, { status: 400 })

  try {
    const response = await fetch(url, {
      method: request.method,
      headers,
      body: isMutationRequest ? await request.bytes() : null,
      redirect: 'manual',
    })

    const responseHeaders = Array.from(response.headers.entries()).filter(
      ([key]) => key.startsWith('content-') || RESPONSE_HEADERS.includes(key)
    )

    // Pass cookies to browser
    response.headers.getSetCookie().forEach(cookie => responseHeaders.push(['set-cookie', cookie]))

    return new NextResponse(response.body, {
      status: response.status,
      headers: responseHeaders,
    })
  } catch (error) {
    console.log(url.toString())
    console.log(error)
    return NextResponse.json({ error: 'Proxy fetch failed' }, { status: 500 })
  }
}

export {
  proxyRequest as GET,
  proxyRequest as POST,
  proxyRequest as PUT,
}
