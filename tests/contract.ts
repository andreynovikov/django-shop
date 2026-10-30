import { readFileSync } from 'fs'
import addFormats from 'ajv-formats'
import OpenAPIBackend, { Document } from 'openapi-backend'

import { schemaCachePath } from './global-setup'

export interface ContractRequest {
  method: string
  path: string // e.g. "/api/v0/users/current/"
  query: Record<string, string | string[]>
  headers: Record<string, string>
  body?: unknown
}

export interface ContractResponse {
  status: number
  body?: unknown
}

interface ValidationError {
  instancePath: string
  message?: string
}

let api: Promise<OpenAPIBackend> | undefined

// drf-spectacular writes OpenAPI 3.0 schemas, Ajv validates JSON Schema: exclusive bounds are numbers there,
// and nullable needs a type
function toJsonSchema(node: unknown): unknown {
  if (Array.isArray(node))
    return node.map(toJsonSchema)
  if (node === null || typeof node !== 'object')
    return node
  const schema: Record<string, unknown> = Object.fromEntries(Object.entries(node).map(([key, value]) => [key, toJsonSchema(value)]))
  for (const [exclusive, bound] of [['exclusiveMaximum', 'maximum'], ['exclusiveMinimum', 'minimum']]) {
    if (typeof schema[exclusive] !== 'boolean')
      continue
    if (schema[exclusive] && typeof schema[bound] === 'number') {
      schema[exclusive] = schema[bound]
      delete schema[bound]
    } else {
      delete schema[exclusive]
    }
  }
  if (schema.nullable === true && schema.type === undefined) {
    delete schema.nullable
    return { anyOf: [schema, { type: 'null' }] }
  }
  return schema
}

function loadApi() {
  api ??= new OpenAPIBackend({
    definition: toJsonSchema(JSON.parse(readFileSync(process.env.API_SCHEMA ?? schemaCachePath, 'utf8'))) as Document,
    // validators are compiled when an operation is first checked
    quick: true,
    // paths of the backend end with a slash, the router would strip it from requests only
    ignoreTrailingSlashes: false,
    ajvOpts: { allErrors: true },
    // drf-spectacular describes a blank email as oneOf an email or an empty string, which needs formats checked
    customizeAjv: (ajv) => {
      addFormats(ajv as unknown as Parameters<typeof addFormats>[0])
      return ajv
    },
  }).init()
  return api
}

const describeErrors = (part: string, errors: ValidationError[] | null | undefined) =>
  (errors ?? []).map(({ instancePath, message }) => `${part}${instancePath} ${message}`)

// Returns how a request of the frontend and the answer of the fake backend differ from the API schema
export async function checkContract(request: ContractRequest, response: ContractResponse) {
  const api = await loadApi()
  const operation = api.matchOperation(request)
  if (operation === undefined)
    return [`${request.method} ${request.path} is not in the API schema`]

  const problems: string[] = []
  try {
    problems.push(...describeErrors('request', api.validateRequest(request, operation).errors))
    const status = String(response.status)
    if (operation.responses?.[status] === undefined && operation.responses?.default === undefined)
      problems.push(`response ${status} is not in the API schema`)
    else if (response.body !== undefined)
      problems.push(...describeErrors(`response ${status} body`, api.validateResponse(response.body, operation, response.status).errors))
  } catch (error) {
    // a schema Ajv can't compile is reported instead of failing the fake request
    problems.push(`can't be checked: ${error instanceof Error ? error.message : error}`)
  }

  return problems.map(problem => `${request.method} ${request.path}: ${problem}`)
}
