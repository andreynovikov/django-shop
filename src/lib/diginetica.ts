const params = {
    apiKey: "OHZ51IBWQJ",
    strategy: "advanced_xname,zero_queries",
    productsSize: 6,
    regionId: "global",
    forIs: true,
    showUnavailable: true,
    unavailableMultiplier: 0.2,
    withContent: true,
    withSku: false
}

const autocompleteUrl = new URL('https://autocomplete.diginetica.net/autocomplete')
Object.entries(params).forEach(([key, value]) => autocompleteUrl.searchParams.set(key, String(value)))

interface CategorySuggestion {
    id: string,
    name: string,
    direct: boolean,
    image_url: string
}

interface ProductSuggestion {
    id: string,
    available: boolean,
    name: string,
    brand: string,
    price: string,
    score: number,
    categories: CategorySuggestion[],
    attributes: Record<string, unknown>,
    link_url: string,
    image_url: string,
    image_urls: string[]
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
    products: ProductSuggestion[],
    categories: CategorySuggestion[],
    brands: unknown[],
    contents: unknown[]
}

export async function loadProductSuggestions(text: string) {
    autocompleteUrl.searchParams.set('st', text)
    const response = await fetch(autocompleteUrl)

    if (!response.ok)
        throw new Error(`HTTP error: ${response}`)

    return await response.json() as Suggestions
}