import { revalidatePath } from 'next/cache'

type Payload = {
  path?: string,
  code?: string,
  uri?: string,
}

type Item = Payload & {
  pk: number | string
}

type RevalidationRequest = Payload & {
  secret: string,
  model: string,
  items?: Item[],
  pk?: number | string
}

type RevalidationResponse = {
  revalidated: boolean,
  message?: string
}

function getPathForModelItem(model: string, item: Item) {
  switch (model) {
    case 'category':
      return `/catalog/${item.path}/`
    case 'product':
      return `/products/${item.code}/`
    case 'page':
      return `/pages${item.uri}`
    case 'news':
      return '/news/'
    default:
      return undefined
  }
}

const respond = (body: RevalidationResponse, status = 200) => Response.json(body, { status })

// The backend posts the saved model items, their pages are rendered again on the next visit
export async function POST(request: Request) {
  const data = await request.json().catch(() => undefined) as RevalidationRequest | undefined
  if (!data)
    return respond({ revalidated: false, message: 'Parameters missing' }, 400)

  if (!process.env.REVALIDATION_TOKEN || data.secret !== process.env.REVALIDATION_TOKEN) {
    return respond({ revalidated: false, message: 'Invalid token' }, 401)
  }

  if (!!!data.model || (data.pk === undefined && data.items === undefined)) {
    return respond({ revalidated: false, message: 'Parameters missing' }, 400)
  }

  const items: Item[] = []
  if (data.pk !== undefined)
    items.push(data as Item)
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
