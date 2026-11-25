export function register() {
  const storefrontName = process.env.STOREFRONT_PROCESS_NAME
  // The container supplies the storefront name so its Node process can be identified on a shared host.
  if (process.env.NEXT_RUNTIME === 'nodejs' && storefrontName) {
    process.title = `nextjs-${storefrontName}`
  }
}
