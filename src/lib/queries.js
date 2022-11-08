import axios from 'axios';

export const userKeys = {
    all: ['users'],
    form: () => [...userKeys.all, 'form'],
    dependencies: () => [...userKeys.all, 'dependencies'], // those queries are invalidated on user login/logout
    references: () => [...userKeys.dependencies(), 'references'], // those queries are reset on user logout
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
    lists: () => [...productKeys.all, 'list'],
    list: (page, size, filters, ordering) => [...productKeys.lists(), { page, size, filters, ordering }],
    suggestions: (text) => [...productKeys.lists(), 'suggestions', text],
    details: () => [...productKeys.all, 'detail'],
    detail: (id) => [...productKeys.details(), id],
    price: (id) => [...productKeys.details(), 'price', id],  // TODO: think how to invalidate it on user change
};

export const basketKeys = {
    all: [...userKeys.dependencies(), 'baskets'],
    details: () => [...basketKeys.all, 'detail'],
};

export const orderKeys = {
    all: [...userKeys.references(), 'orders'],
    lists: () => [...orderKeys.all, 'list'],
    list: (page, filter) => [...orderKeys.lists(), { page, filter }],
    last: () => [...orderKeys.lists(), 'last'],
    details: () => [...orderKeys.all, 'detail'],
    detail: (id) => [...orderKeys.details(), id],
};

export const favoriteKeys = {
    all: [...userKeys.references(), 'favorites'],
    details: () => [...favoriteKeys.all, 'detail'],
};

export const comparisonKeys = {
    all: [...userKeys.references(), 'comparisons'],
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
    console.log(response.data);
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

export async function loadOrders(page, filter) {
    const url = new URL(API + 'orders/');
    if (+page !== 1)
        url.searchParams.set('page', page);
    if (filter !== undefined && filter !== '')
        url.searchParams.set('filter', filter);
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

export async function getProductPrice(id) {
    const response = await apiClient.get(`products/${id}/price/`);
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
