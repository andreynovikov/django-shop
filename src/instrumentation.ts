export function register() {
  const storefrontName = process.env.STOREFRONT_PROCESS_NAME
  if (process.env.NEXT_RUNTIME === 'nodejs' && storefrontName) {
    process.title = `nextjs-${storefrontName}`
  }
}
