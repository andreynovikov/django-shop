const suggestionParams = {
    apiKey: 'OHZ51IBWQJ',
    strategy: 'advanced_xname,zero_queries',
    productsSize: 6,
    regionId: 'global',
    forIs: true,
    showUnavailable: true,
    unavailableMultiplier: 0.2,
    withContent: true,
    withSku: false
}

const searchParams = {
    apiKey: 'OHZ51IBWQJ',
    strategy: 'advanced_xname,zero_queries',
    fullData: true,
    withCorrection: true,
    withSku: false,
    withFacets: true,
    treeFacets: true,
    useCategoryPrediction: false,
    regionId: 'global',
    unavailableMultiplier: 0.2,
    preview: false,
    sort: 'DEFAULT'
}

const autocompleteUrl = new URL('https://autocomplete.diginetica.net/autocomplete')
Object.entries(suggestionParams).forEach(([key, value]) => autocompleteUrl.searchParams.set(key, String(value)))

const searchUrl = new URL('https://sort.diginetica.net/search')
Object.entries(searchParams).forEach(([key, value]) => searchUrl.searchParams.set(key, String(value)))

interface Category {
    id: string,
    name: string,
    direct: boolean,
    image_url: string
}

export interface ProductResult {
    id: string,
    available: boolean,
    name: string,
    brand: string,
    price: string,
    score: number,
    categories: Category[],
    attributes: Record<string, unknown>,
    link_url: string,
    image_url: string,
    image_urls: string[]
}

interface FacetValue {
    id: string,
    name: string,
    value: number,
    pictureUrl?: number,
    open?: boolean,
    selected?: boolean
}

interface Facet {
    name: string,
    dataType: 'SLIDER' | 'DISTINCT',
    values: FacetValue[]
}

export interface Suggestions {
    query: string,
    correction?: string,
    sts: {
        st: string,
        amount: string
    }[],
    taps: {
        tap: string,
        relatedSearch: string
    }[],
    products: ProductResult[],
    categories: Category[],
    brands: unknown[],
    contents: unknown[]
}

export interface Results {
  query: string,
  correction: string,
  totalHits: number,
  zeroQueries: boolean,
  products: ProductResult[],
  facets: Facet[],
  selectedFacets: unknown[]
}

export async function loadProductSuggestions(text: string) {
    autocompleteUrl.searchParams.set('st', text)
    const response = await fetch(autocompleteUrl)

    if (!response.ok)
        throw new Error(`HTTP error: ${response}`)

    return await response.json() as Suggestions
}

export async function loadProducts(text: string, page: number = 1, pageSize: number = 15, filters: Record<string, unknown>) {
    searchUrl.searchParams.set('st', text)
    searchUrl.searchParams.set('offset', String((page - 1) * pageSize))
    searchUrl.searchParams.set('size', String(pageSize))

    searchUrl.searchParams.set('showUnavailable', String(!filters?.available))
    searchUrl.searchParams.delete('filter')
    if (filters?.price)
        searchUrl.searchParams.append('filter', `price:${(filters.price as number[])[0]};${(filters.price as number[])[1]}`)
    if (filters?.manufacturer)
        searchUrl.searchParams.append('filter', `brands:${(filters.manufacturer as string[]).join(';')}`)

    const response = await fetch(searchUrl)

    if (!response.ok)
        throw new Error(`HTTP error: ${response}`)

    return await response.json() as Results
}