import type { NextApiRequest, NextApiResponse } from 'next'

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
    default:
      return undefined
  }
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<RevalidationResponse>
) {
  const data = req.body as RevalidationRequest
  if (data === undefined)
    return res.status(400).json({ revalidated: false, message: 'Parameters missing' })

  if (!process.env.REVALIDATION_TOKEN || data.secret !== process.env.REVALIDATION_TOKEN) {
    return res.status(401).json({ revalidated: false, message: 'Invalid token' })
  }

  if (!!!data.model || (data.pk === undefined && data.items === undefined)) {
    return res.status(400).json({ revalidated: false, message: 'Parameters missing' })
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

  // Revalidate every path independently so one failure does not skip the rest.
  // If there was an error, Next.js will continue to show the last successfully generated page
  const failed: string[] = []
  for (const path of paths) {
    try {
      await res.revalidate(path)
    } catch (err) {
      console.error('Failed to revalidate', path, err)
      failed.push(path)
    }
  }

  const problems = []
  if (unmapped.length > 0)
    problems.push(`No path for ${data.model} ${unmapped.join(', ')}`)
  if (failed.length > 0)
    problems.push(`Revalidation error for ${failed.join(', ')}`)

  if (problems.length > 0)
    return res.status(failed.length > 0 ? 500 : 200).json({ revalidated: false, message: problems.join('; ') })
  return res.json({ revalidated: true })
}
