import path from 'path'
import ejs from 'ejs'

import { listIntegrations, retriveIntegrationByUtm, retriveIntegrationProducts } from "@/lib/token-queries"
import { AxiosError } from 'axios'

export const revalidate = 3600
export const dynamic = 'error'

const rootDirectory = process.cwd()

export async function GET(
  request: Request,
  { params }: RouteContext<'/xml/[filename]'>
) {
  const { filename } = await params
  const utm = path.parse(filename).name
  try {
    const integration = await retriveIntegrationByUtm(utm)
    const products = await retriveIntegrationProducts(integration.id)

    const data = {
      utm_source: utm,
      integration,
      products,
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
      return Response.json({ error: 'Not found' }, { status: 404 });
    else
      return Response.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}

export async function generateStaticParams() {
  const integrations = await listIntegrations()
  return integrations.map(integration => ({ utm: integration.utm_source }))
}
