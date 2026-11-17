import { NextRequest } from 'next/server'
import { revalidatePath, revalidateTag } from 'next/cache'

import { apiFetch } from '@/lib/queries'
import { AnonymousUser, User } from '@/lib/types'

type LegacyItem = {
  pk: number | string
  path?: string
  code?: string
  uri?: string
}

type RevalidationRequest = {
  secret: string
  // tags of the data that changed, see lib/queries/cache-tags.ts
  tags?: string[]
  // stale-while-revalidate: the next visit gets the page as it was and has it rendered again; otherwise it waits
  background?: boolean
  // TODO: remove once django-shop sends tags: a saved model item, by the paths of its pages
  model?: string
  items?: LegacyItem[]
  pk?: number | string
} & Omit<LegacyItem, 'pk'>

type RevalidationResponse = {
  revalidated: boolean
  message?: string
}

function getPathForModelItem(model: string, item: LegacyItem) {
  switch (model) {
    case 'index':
      return '/'
    case 'category':
      return `/catalog/${item.path}/`
    case 'product':
      return `/products/${item.code}/`
    case 'store':
      return `/stores/${item.pk}/`
    case 'page':
      return `/pages${item.uri}`
    case 'news':
      return '/news/'
    case 'actions':
      return `/actions/`
    case 'stores':
      return `/stores/`
    default:
      return undefined
  }
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

  if (Array.isArray(data.tags)) {
    const tags = data.tags.filter(tag => typeof tag === 'string' && tag.length > 0)
    console.log('Revalidating', data.background ? 'in the background' : 'at once', tags)
    for (const tag of tags)
      revalidateTag(tag, data.background ? 'max' : { expire: 0 })
    return respond({ revalidated: true })
  }

  if (!!!data.model || (data.pk === undefined && data.items === undefined)) {
    return respond({ revalidated: false, message: 'Parameters missing' }, 400)
  }

  const items: LegacyItem[] = []
  if (data.pk !== undefined)
    items.push(data as LegacyItem)
  if (data.items !== undefined)
    items.push(...data.items)

  const paths = new Set<string>()
  const unmapped: (number | string | undefined)[] = []
  for (const item of items) {
    const path = getPathForModelItem(data.model, item)
    if (path === undefined)
      unmapped.push(item.pk)
    else
      paths.add(path)
  }

  console.log('Revalidating', data.model, [...paths])

  for (const path of paths)
    revalidatePath(path)

  if (unmapped.length > 0)
    return respond({ revalidated: false, message: `No path for ${data.model} ${unmapped.join(', ')}` })
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
