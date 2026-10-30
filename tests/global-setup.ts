import { mkdir, stat, writeFile } from 'fs/promises'
import path from 'path'

// Contract checks validate the fake backend against the OpenAPI schema of the real one, see contract.ts
export const schemaCachePath = path.resolve(__dirname, '.cache/openapi.json')

// Generating the schema takes the backend a while, so a downloaded copy is reused for an hour
const SCHEMA_MAX_AGE = 60 * 60 * 1000

export default async function globalSetup() {
  // API_SCHEMA is a local schema file instead, e.g. from `manage.py spectacular` before deploying the backend
  if (process.env.API_SCHEMA)
    return

  const cached = await stat(schemaCachePath).catch(() => undefined)
  if (cached !== undefined && Date.now() - cached.mtimeMs < SCHEMA_MAX_AGE)
    return

  try {
    const response = await fetch(`${process.env.API_SERVER}/api/v0/schema/?format=json`, {
      headers: { authorization: `Token ${process.env.API_TOKEN}` },
      signal: AbortSignal.timeout(120_000),
    })
    if (!response.ok)
      throw new Error(`HTTP ${response.status} ${response.statusText}`)
    await mkdir(path.dirname(schemaCachePath), { recursive: true })
    await writeFile(schemaCachePath, await response.text())
  } catch (error) {
    if (cached === undefined)
      throw new Error(`Contract checks need the API schema, and downloading it failed: ${error}`)
    console.warn(`Using the API schema downloaded ${cached.mtime.toISOString()}, downloading a new one failed: ${error}`)
  }
}
