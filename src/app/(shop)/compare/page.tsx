import ProductComparison from '@/components/product/comparison'

// The page is static, the products to compare are read from the query and loaded in the browser.
// Reading the query needs a Suspense boundary, loading.tsx is the one.
export default function ComparePage() {
  return <ProductComparison />
}
