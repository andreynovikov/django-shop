import path from 'path'
import ejs from 'ejs'
import sanitizeHtml from 'sanitize-html'

import { AxiosError } from 'axios'

import { loadCategories, loadCurrentSite } from '@/lib/queries'
import { listIntegrations, retriveIntegrationByUtm, retriveIntegrationProducts } from "@/lib/token-queries"
import { Category } from '@/lib/types'

export const revalidate = 3600
export const dynamic = 'error'

const rootDirectory = process.cwd()

function flattenCategoryTree(categories: Category[]) {
  return categories.reduce((acc, category) => {
    const { children, ...categoryWithoutChildren } = category
    acc.push(categoryWithoutChildren);
    if (children) {
      acc.push(...flattenCategoryTree(children))
    }
    return acc
  }, [] as Category[])
}

function stripTags(html: string) {
  return sanitizeHtml(html, { allowedTags: [], allowedAttributes: {} })
}

function topCategoryMap(categories: Category[]) {
  const map = new Map<number, Category>()
  for (const category of categories) {
    const { children, ...categoryWithoutChildren } = category
    if (children) {
      flattenCategoryTree(children).forEach(child => {
        map.set(child.id, categoryWithoutChildren)
      })
    }
    map.set(category.id, categoryWithoutChildren)
  }
  return map
}

export async function GET(
  request: Request,
  { params }: RouteContext<'/xml/[filename]'>
) {
  const { filename } = await params
  const utm = path.parse(filename).name
  try {
    const site = await loadCurrentSite()
    const integration = await retriveIntegrationByUtm(utm)
    if (!integration.enabled)
      return Response.json({ error: 'Not found' }, { status: 404 })
    const products = await retriveIntegrationProducts(integration.id)
    const categories = integration.output_skip_categories ? [] : await loadCategories({feed: true}) as Category[]
    const categoryMap = topCategoryMap(categories)

    const getTopCategories = (categories: number[]) => {
      const topCategories = categories.map(category => categoryMap.get(category)).filter(category => category !== undefined)
      return  [...new Set(topCategories)]
    }

    const data = {
      utm_source: utm,
      site,
      integration,
      categories,
      products,
      getTopCategories,
      stripTags,
    }
    const template = path.join(rootDirectory, 'templates', 'xml', `${integration.output_template}.ejs`)
    const xml = await ejs.renderFile(template, data, { rmWhitespace: true })

    return new Response(
      xml,
      {
        headers: {
          'Content-Type': 'text/xml',
        },
      })
  } catch (error) {
    console.error(error)
    if (error instanceof AxiosError || (error instanceof Error && 'code' in error && error.code === 'ENOENT'))
      return Response.json({ error: 'Not found' }, { status: 404 })
    else
      return Response.json({ error: 'Internal Server Error' }, { status: 500 })
  }
}

export async function generateStaticParams() {
  const integrations = await listIntegrations()
  return integrations.filter(integration => integration.enabled).map(integration => ({ utm: integration.utm_source }))
}
