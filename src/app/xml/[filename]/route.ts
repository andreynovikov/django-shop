import path from 'path'
import ejs from 'ejs'
import sanitizeHtml from 'sanitize-html'

import { AxiosError } from 'axios'

import { loadCategories, loadCurrentSite, loadProducts } from '@/lib/queries'
import { listIntegrations, retriveIntegrationByUtm, retriveIntegrationProducts } from "@/lib/token-queries"
import { Category, Integration, Product } from '@/lib/types'

export const revalidate = 3600
export const dynamic = 'error'

const rootDirectory = process.cwd()
const globalXmls = [
  'products',
  'search',
]

interface CategoryWithParent extends Category {
  parent: number | null
  path: string[]
}


function flattenCategoryTree(parent: Category, parentPath: string[], categories: Category[]) {
  return categories.reduce((acc, category) => {
    const { children, ...categoryWithoutChildren } = category
    const categoryPath = [...parentPath, categoryWithoutChildren.slug]
    acc.push({
      ...categoryWithoutChildren,
      parent: parent.id,
      path: categoryPath,
    })
    if (children) {
      acc.push(...flattenCategoryTree(categoryWithoutChildren, categoryPath, children))
    }
    return acc
  }, [] as CategoryWithParent[])
}

function stripTags(html: string) {
  return sanitizeHtml(html, { allowedTags: [], allowedAttributes: {} })
}

function topCategoryMap(categories: Category[]) {
  const map = new Map<number, Category>()
  for (const category of categories) {
    const { children, ...categoryWithoutChildren } = category
    if (children) {
      flattenCategoryTree(categoryWithoutChildren, [category.slug], children).forEach(child => {
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

  let integration: Integration | undefined
  let products: Product[]
  let templateName = utm

  try {
    const site = await loadCurrentSite()
    if (!globalXmls.includes(utm)) {
      integration = await retriveIntegrationByUtm(utm)
      if (!integration.enabled)
        return Response.json({ error: 'Not found' }, { status: 404 })
      templateName = integration.output_template
    }

    const categories = integration?.output_skip_categories ? [] : await loadCategories({ feed: true }) as Category[]
    const categoryMap = topCategoryMap(categories)

    if (integration) {
      products = await retriveIntegrationProducts(integration.id)
    } else {
      products = []
      const filters = {
        for_xml: true,
        enabled: true,
        price: [0, 10000000],
        in_category: categories.map(category => category.id),
        variations: '',
      }
      const pageSize = 1000
      const order = 'id'
      let currentPage = 1
      while (true) {
        const productsPage = await loadProducts(currentPage, pageSize, filters, order)
        console.log(productsPage.currentPage)
        products.push(...productsPage.results)
        if (productsPage.totalPages <= currentPage)
          break;
        currentPage++
      }
    }

    const getTopCategories = (categories: number[]) => {
      const topCategories = categories.map(category => categoryMap.get(category)).filter(category => category !== undefined)
      return [...new Set(topCategories)]
    }

    const getCategoryDescendants = (category: Category) => {
      const { children, ...categoryWithoutChildren } = category
      if (children)
        return flattenCategoryTree(categoryWithoutChildren, [category.slug], children)
      else
        return []
    }

    const data = {
      utm_source: utm,
      site,
      integration,
      categories,
      products,
      getTopCategories,
      getCategoryDescendants,
      stripTags,
    }
    const template = path.join(rootDirectory, 'templates', 'xml', `${templateName}.ejs`)
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
  return integrations.filter(
    integration => integration.enabled
  ).map(
    integration => ({ utm: integration.utm_source })
  ).concat(
    globalXmls.map(xml => ({ utm: xml }))
  )
}
