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

function getPathForModelItem(model: string, item: Payload) {
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

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<RevalidationResponse>
) {
  const data = req.body as RevalidationRequest
  if (data === undefined)
    return res.status(400).json({ revalidated: false, message: 'Parameters missing' })

  console.log(data)
  if (data.secret !== process.env.REVALIDATION_TOKEN) {
    return res.status(401).json({ revalidated: false, message: 'Invalid token' })
  }

  if (!!!data.model || (data.pk === undefined && data.items === undefined)) {
    return res.status(400).json({ revalidated: false, message: 'Parameters missing' })
  }

  const paths = []
  if (data.pk !== undefined)
    paths.push(getPathForModelItem(data.model, data))
  if (data.items !== undefined)
    data.items.forEach(item => paths.push(getPathForModelItem(data.model, item)))

  try {
    for (const path of paths) {
      if (path === undefined)
        return res.json({ revalidated: false })
      await res.revalidate(path)
    }
  } catch (err) {
    // If there was an error, Next.js will continue
    // to show the last successfully generated page
    console.error(err)
    return res.status(500).send({ revalidated: false, message: 'Revalidation error' })
  }
}
