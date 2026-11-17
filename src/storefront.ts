// What this storefront has, for the components that every storefront shares. Of those, it is the only file
// that differs between storefronts, so the others are copied as they are.
export const storefront = {
  favorites: false, // the account has a favorites page
  productPages: true, // products have their own pages, so carts and orders link to them
  // the backend filters of the products this storefront lists, `baseFilters` in lib/catalog
  productFilters: {
    enabled: true,
  },
}
