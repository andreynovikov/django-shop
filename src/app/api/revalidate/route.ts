import { NextRequest } from 'next/server'
import { revalidatePath, revalidateTag } from 'next/cache'

import { apiFetch } from '@/lib/queries'
import { AnonymousUser, User } from '@/lib/types'

type RevalidationRequest = {
  secret: string
  // tags of the data that changed, see lib/queries/cache-tags.ts
  tags: string[]
  // stale-while-revalidate: the next visit gets the page as it was and has it rendered again; otherwise it waits
  background?: boolean
}

type RevalidationResponse = {
  revalidated: boolean
  message?: string
}

const respond = (body: RevalidationResponse, status = 200) => Response.json(body, { status })

// The backend posts the tags of the data that changed, the pages that used them are rendered again
export async function POST(request: Request) {
  const data = await request.json().catch(() => undefined) as RevalidationRequest | undefined
  if (!data)
    return respond({ revalidated: false, message: 'Parameters missing' }, 400)

  if (!process.env.REVALIDATION_TOKEN || data.secret !== process.env.REVALIDATION_TOKEN) {
    return respond({ revalidated: false, message: 'Invalid token' }, 401)
  }

  if (!Array.isArray(data.tags))
    return respond({ revalidated: false, message: 'Parameters missing' }, 400)

  const tags = data.tags.filter(tag => typeof tag === 'string' && tag.length > 0)
  console.log('Revalidating', data.background ? 'in the background' : 'at once', tags)
  for (const tag of tags)
    revalidateTag(tag, data.background ? 'max' : { expire: 0 })
  return respond({ revalidated: true })
}

// Staff open /api/revalidate/?path=/catalog/sewing/ to have the page rendered again and see it, with &all every page
// of the site. Next keeps pages under their route files, not their urls, so a part of the site can't be asked for:
// /catalog/sewing/2/ is a page of its own. Django tells from the session cookie who it is.
export async function GET(request: NextRequest) {
  const all = request.nextUrl.searchParams.has('all')
  const path = request.nextUrl.searchParams.get('path') ?? (all ? '/' : null)
  // a path of this site only, the answer redirects to it
  if (!path || !path.startsWith('/') || path.startsWith('//') || path.includes('\\'))
    return respond({ revalidated: false, message: 'Path missing' }, 400)

  const user = await apiFetch<AnonymousUser | User>('users/current/', {
    headers: { cookie: request.headers.get('cookie') ?? '' },
    cache: 'no-store',
  }).catch(() => undefined)
  if (!user || user.is_anonymous || !user.is_staff)
    return respond({ revalidated: false, message: 'Staff only' }, 403)

  if (all) {
    revalidatePath('/', 'layout') // the root layout is in every page
  } else {
    // pages are cached under the path as it was requested, which encodes letters other than Latin
    const variants = new Set([path])
    try {
      variants.add(encodeURI(decodeURI(path)))
    } catch {
      // a malformed escape, the path as it is
    }
    for (const variant of variants)
      revalidatePath(variant)
  }
  console.log('Revalidated by user', user.id, all ? 'every page' : path)

  return new Response(null, { status: 303, headers: { location: path, 'cache-control': 'no-store' } })
}
