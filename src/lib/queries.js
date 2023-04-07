import axios from 'axios';

export const userKeys = {
    all: ['users'],
    form: () => [...userKeys.all, 'form'],
    details: () => [...userKeys.all, 'detail'],
    detail: (id) => [...userKeys.details(), id],
    check: (phone) => [...userKeys.details(), 'check', phone],
    current: () => [...userKeys.details(), 'current'],
};

export const categoryKeys = {
    all: ['categories'],
    lists: () => [...categoryKeys.all, 'list'],
    details: () => [...categoryKeys.all, 'detail'],
    detail: (path) => [...categoryKeys.details(), path],
};

export const productKeys = {
    all: ['products'],
    fields: () => [...productKeys.all, 'fields'],
    suggestions: (text) => [...productKeys.all, 'suggestions', text],
    images: (id) => [...productKeys.all, id, 'images'],
    stock: (id) => [...productKeys.all, id, 'stock'],
    lists: () => [...productKeys.all, 'list'],
    list: (page, size, filters, ordering) => [...productKeys.lists(), { page, size, filters, ordering }],
    details: () => [...productKeys.all, 'detail'],
    detail: (id) => [...productKeys.details(), id]
};

export const reviewKeys = {
    all: ['reviews'],
    lists: () => [...reviewKeys.all, 'list'],
    list: (productId) => [...reviewKeys.lists(), { productId }],
    rating: (productId) => [...reviewKeys.list(productId), 'rating'],
    form: (productId) => [...reviewKeys.list(productId), 'form'],
    details: () => [...reviewKeys.all, 'detail'],
    detail: (productId, id) => [...reviewKeys.details(), { productId, id }],
};

export const basketKeys = {
    all: ['baskets'],
    details: () => [...basketKeys.all, 'detail'],
};

export const orderKeys = {
    all: ['orders'],
    lists: () => [...orderKeys.all, 'list'],
    list: (page, filter) => [...orderKeys.lists(), { page, filter }],
    last: () => [...orderKeys.lists(), 'last'],
    details: () => [...orderKeys.all, 'detail'],
    detail: (id) => [...orderKeys.details(), id],
};

export const favoriteKeys = {
    all: ['favorites'],
    details: () => [...favoriteKeys.all, 'detail'],
};

export const comparisonKeys = {
    all: ['comparisons'],
    lists: () => [...comparisonKeys.all, 'list'],
    list: (kind) => [...comparisonKeys.lists(), kind]
};

export const kindKeys = {
    all: ['kinds'],
    lists: () => [...kindKeys.all, 'list'],
    list: (filter) => [...kindKeys.lists(), filter],
    details: () => [...kindKeys.all, 'detail'],
    detail: (id) => [...kindKeys.details(), id],
};

export const pageKeys = {
    all: ['pages'],
    lists: () => [...pageKeys.all, 'list'],
    details: () => [...pageKeys.all, 'detail'],
    detail: (uri) => [...pageKeys.details(), uri],
};

export const newsKeys = {
    all: ['news'],
    lists: () => [...newsKeys.all, 'list'],
};

export const blogKeys = {
    all: ['blog'],
    lists: () => [...blogKeys.all, 'list'],
    list: (page, filters) => [...blogKeys.lists(), { page, filters }],
    details: () => [...blogKeys.all, 'detail'],
    detail: (uri) => [...blogKeys.details(), uri],
    tags: () => [...blogKeys.lists(), 'tags'],
    categories: () => [...blogKeys.lists(), 'categories'],
    category: (slug) => [...blogKeys.categories(), slug],
};

export const storeKeys = {
    all: ['stores'],
    lists: () => [...storeKeys.all, 'list'],
    details: () => [...storeKeys.all, 'detail'],
    detail: (id) => [...storeKeys.details(), id],
};

export const serviceCenterKeys = {
    all: ['serviceCenters'],
    lists: () => [...serviceCenterKeys.all, 'list'],
    details: () => [...serviceCenterKeys.all, 'detail'],
    detail: (id) => [...serviceCenterKeys.details(), id],
};

export const siteKeys = {
    all: ['sites'],
    current: () => [...siteKeys.all, 'current'],
};

// those queries are reset on user logout
export const userReferences = [
    orderKeys.all,
    favoriteKeys.all,
    comparisonKeys.all
];

// those queries are invalidated on user login/logout
export const userDependencies = [
    productKeys.lists(),
    productKeys.details(),
    basketKeys.all
];

export function normalizePhone(phone) {
    phone = phone.replaceAll(/[^0-9\+]/g, '');
    if (!phone.startsWith('+')) {
        if (phone.startsWith('7') && phone.length === 11)
            phone = '+' + phone
        else
            phone = '+7' + phone
    }
    return phone;
};

export const API = process.env.NEXT_PUBLIC_API;

export const apiClient = axios.create({
    baseURL: API,
    withCredentials: true,
});

apiClient.defaults.headers.post['Content-Type'] = 'application/json';
apiClient.defaults.headers.put['Content-Type'] = 'application/json';

apiClient.interceptors.request.use(async function (config) {
    if (typeof window === 'undefined') {// set referrer when running on server
        config.headers['Referer'] = process.env.NEXT_PUBLIC_ORIGIN;
        config.headers['Origin'] = process.env.NEXT_PUBLIC_ORIGIN;
    }
    if (config.method === 'post' || config.method === 'put') {
        const response = await axios.get(API + 'csrf/', { withCredentials: true });
        config.headers['X-CSRFTOKEN'] = response.data.csrf;
    }
    return config;
}, function (error) {
    return Promise.reject(error);
});

export async function loadBasket() {
    const response = await apiClient.get('baskets/');
    return response.data;
}

export async function createBasket() {
    const response = await apiClient.post('baskets/');
    return response.data;
}

export async function addBasketItem(basketId, product, quantity) {
    const response = await apiClient.post(`baskets/${basketId}/add/`, {
        product,
        quantity
    });
    return response.data;
}

export async function removeBasketItem(basketId, product) {
    const response = await apiClient.post(`baskets/${basketId}/remove/`, {
        product
    });
    return response.data;
}

export async function updateBasketItem(basketId, product, quantity) {
    const response = await apiClient.post(`baskets/${basketId}/update/`, {
        product,
        quantity
    });
    return response.data;
}

export async function createOrder() {
    const response = await apiClient.post('orders/');
    return response.data;
}

export async function loadOrders(page, filter, site=undefined) {
    const url = new URL(API + 'orders/');
    if (+page !== 1)
        url.searchParams.set('page', page);
    if (filter !== undefined && filter !== '')
        url.searchParams.set('filter', filter);
    if (site !== undefined)
        url.searchParams.set('site', site);
    const response = await apiClient.get(url);
    return response.data;
};

export async function getLastOrder() {
    const response = await apiClient.post('orders/last/');
    return response.data;
}

export async function loadOrder(id) {
    const response = await apiClient.get(`orders/${id}/`);
    return response.data;
}

export async function updateOrder(id, data) {
    const response = await apiClient.put('orders/' + id + '/', data);
    return response.data;
}

export async function loadFavorites() {
    const response = await apiClient.get('favorites/');
    return response.data;
}

export async function addToFavorites(product) {
    const response = await apiClient.post('favorites/add/', {
        product
    });
    return response.data;
}

export async function removeFromFavorites(product) {
    const response = await apiClient.post('favorites/remove/', {
        product
    });
    return response.data;
}

export async function loadComparisons(kind) {
    const url = new URL(API + 'comparisons/');
    if (kind !== null)
        url.searchParams.set('kind', kind);
    const response = await apiClient.get(url);
    return response.data;
}

export async function addToComparison(product) {
    const response = await apiClient.post('comparisons/add/', {
        product
    });
    return response.data;
}

export async function removeFromComparison(product) {
    const response = await apiClient.post('comparisons/remove/', {
        product
    });
    return response.data;
}

export async function loadCategories() {
    const response = await apiClient.get('categories/');
    return response.data;
}

export async function loadCategory(path) {
    const response = await apiClient.get(`categories/${path.join('/')}/`);
    return response.data;
}

export async function loadKinds(productIds) {
    const url = new URL(API + 'kinds/');
    for (const value of productIds)
        url.searchParams.append('product', value);
    const response = await apiClient.get(url);
    return response.data;
}

export async function loadKind(id) {
    const response = await apiClient.get('kinds/' + id + '/');
    return response.data;
}

export async function loadProducts(page, pageSize, filters, ordering) {
    const url = new URL(API + 'products/');

    if (filters != null)
        for (var filter of filters)
            if (Array.isArray(filter.value)) {
                for (const value of filter.value)
                    url.searchParams.append(filter.field, value);
            } else {
                url.searchParams.append(filter.field, filter.value);
            }
    if (page != null)
        url.searchParams.set('page', page);
    if (pageSize != null)
        url.searchParams.set('page_size', pageSize);
    if (ordering != null)
        url.searchParams.set('ordering', ordering);
    const response = await apiClient.get(url.toString());
    return response.data;
}

export async function loadProductSuggestions(text) {
    const url = new URL(API + 'products/');
    url.searchParams.set('title', text);
    url.searchParams.set('ta', 1);
    url.searchParams.set('page_size', 10);
    const response = await apiClient.get(url.toString());
    return response.data;
}

export async function getProductImages(id) {
    const response = await apiClient.get(`products/${id}/images/`);
    return response.data;
}

export async function loadProductStock(id) {
    const response = await apiClient.get(`products/${id}/stock/`);
    return response.data;
}

export async function getProductRating(id) {
    const response = await apiClient.get(`reviews/shop.product/${id}/average/`);
    return response.data;
}

export async function getReviewForm(id) {
    const response = await apiClient.get(`reviews/shop.product/${id}/form/`);
    return response.data;
}

export async function createProductReview(id, data) {
    const response = await apiClient.post(`reviews/shop.product/${id}/`, data);
    return response.data;
}

export async function loadProductReviews(id) {
    const response = await apiClient.get(`reviews/shop.product/${id}/`);
    return response.data;
}

export async function loadProductReview(id, reviewId) {
    const response = await apiClient.get(`reviews/shop.product/${id}/${reviewId}/`);
    return response.data;
}

export async function updateProductReview(id, reviewId, data) {
    const response = await apiClient.put(`reviews/shop.product/${id}/${reviewId}/`, data);
    return response.data;
}

export async function loadPromoReviews() {
    const response = await apiClient.get("reviews/?model=shop.product&user=1&site=10&page_size=10");
    return response.data;
}

export async function loadProduct(id) {
    const response = await apiClient.get(`products/${id}/`);
    return response.data;
}

export async function loadProductByCode(code) {
    const response = await apiClient.get(`products/${code}/bycode/`);
    return response.data;
}

export async function getProductFields() {
    const response = await apiClient.get('products/fields/');
    return response.data;
}

export async function checkUser(phone, reset) {
    const response = await apiClient.post('users/' + normalizePhone(phone) + '/check/', {
        reset
    });
    return response.data;
}

export async function currentUser() {
    const response = await apiClient.get('users/current/');
    return response.data;
}

export async function getUserForm() {
    const response = await apiClient.get('users/form/');
    return response.data;
}

export async function loadUser(id) {
    const response = await apiClient.get('users/' + id + '/');
    return response.data;
}

export async function updateUser(id, data) {
    const response = await apiClient.put('users/' + id + '/', data);
    return response.data;
}

export async function loadPages() {
    const response = await apiClient.get('pages/');
    return response.data;
}

export async function loadPage(uri) {
    const response = await apiClient.get(`pages/${uri.join('/')}/`);
    return response.data;
}

export async function loadNews() {
    const response = await apiClient.get('news/');
    return response.data;
}

export async function loadBlogTags() {
    const response = await apiClient.get('blog/tags/');
    return response.data;
}

export async function loadBlogCategories() {
    const response = await apiClient.get('blog/categories/');
    return response.data;
}

export async function loadBlogCategory(slug) {
    const response = await apiClient.get(`blog/categories/${slug}/`);
    return response.data;
}

export async function loadBlogEntries(page, filters) {
    const url = new URL(API + 'blog/entries/');
    if (page !== null && +page !== 1)
        url.searchParams.set('page', page);
    if (filters !== null)
        for (var filter of filters)
            if (Array.isArray(filter.value)) {
                for (const value of filter.value)
                    url.searchParams.append(filter.field, value);
            } else {
                url.searchParams.append(filter.field, filter.value);
            }
    const response = await apiClient.get(url);
    return response.data;
};

export async function loadBlogEntry(uri) {
    const response = await apiClient.get(`blog/entries/${uri.join('/')}/`);
    return response.data;
}

export async function loadStores() {
    const response = await apiClient.get('stores/');
    return response.data;
}

export async function loadStore(id) {
    const response = await apiClient.get('stores/' + id + '/');
    return response.data;
}

export async function loadServiceCenters() {
    const response = await apiClient.get('servicecenters/');
    return response.data;
}

export async function loadServiceCenter(id) {
    const response = await apiClient.get('servicecenters/' + id + '/');
    return response.data;
}

export async function loadCurrentSite() {
    const response = await apiClient.get('sites/current/');
    return response.data;
}

export async function getWarrantyCard(code) {
    return apiClient.get(`warrantycard/${encodeURIComponent(code)}/`);
}
