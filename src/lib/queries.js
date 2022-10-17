import { getSession } from 'next-auth/react';

import axios from 'axios';

export const categoryKeys = {
    all: ['categories'],
    lists: () => [...categoryKeys.all, 'list'],
    details: () => [...categoryKeys.all, 'detail'],
    detail: (path) => [...categoryKeys.details(), path],
};

export const productKeys = {
    all: ['products'],
    lists: () => [...productKeys.all, 'list'],
    list: (page, size, filters, ordering) => [...productKeys.lists(), { page, size, filters, ordering }],
    details: () => [...productKeys.all, 'detail'],
    detail: (id) => [...productKeys.details(), id],
    price: (id) => [...productKeys.details(), 'price', { id }],
};

export const basketKeys = {
    all: ['baskets'],
    details: () => [...basketKeys.all, 'detail'],
    detail: () => [...basketKeys.details(), ''],
};

export const userKeys = {
    all: ['users'],
    details: () => [...userKeys.all, 'detail'],
    detail: (phone) => [...userKeys.details(), phone],
    check: (phone) => [...userKeys.details(), 'check', phone],
    current: () => [...userKeys.details(), 'current'],
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

export const API = process.env.NEXT_PUBLIC_ORIGIN + 'api/v0/'; // 'https://cartzilla.sigalev.ru/api/v0/';

export const apiClient = axios.create({
    baseURL: API,
    withCredentials: true,
});
apiClient.defaults.headers.common['Content-Type'] = 'application/json';

apiClient.interceptors.request.use(function (config) {
    if (!!!process.client)
        config.headers['Referer'] = process.env.NEXT_PUBLIC_ORIGIN;
    return config;
}, function (error) {
    return Promise.reject(error);
});

export async function withClient(handler, ...params) {
    return handler(...params, apiClient);
}

export async function withAuthClient(handler, ...params) {
    return withClient(async (...params) => {
        const session = await getSession();
        const client = params.pop();
        const authClient = axios.create(client.defaults);
        console.log(session);
        if (session?.accessToken)
            authClient.defaults.headers.common['Authorization'] = `Bearer ${session.accessToken}`;
        return handler(...params, authClient);
    }, ...params);
    /*
        const session = await getSession()
        if (!session) {
            return Promise.reject("Unauthorized");
        }
    */
}

export async function withSession(session, handler, ...params) {
    // https://stackoverflow.com/a/59712429/488489
    return withClient(async (...params) => {
        const client = params.pop();
        const authClient = axios.create(client.defaults);
        if (session?.accessToken)
            authClient.defaults.headers.common['Authorization'] = `Bearer ${session.accessToken}`;
        return handler(...params, authClient);
    }, ...params);
}

export async function loadBasket(client) {
    const response = await client.get('baskets/');
    return response.data;
}

export async function createBasket(client) {
    const response = await client.post('baskets/');
    console.log(response.data);
    return response.data;
}

export async function addBasketItem(basketId, product, quantity, client) {
    const response = await client.post(`baskets/${basketId}/add/`, {
        product,
        quantity
    });
    return response.data;
}

export async function removeBasketItem(basketId, product, client) {
    const response = await client.post(`baskets/${basketId}/remove/`, {
        product
    });
    return response.data;
}

export async function updateBasketItem(basketId, product, quantity, client) {
    const response = await client.post(`baskets/${basketId}/update/`, {
        product,
        quantity
    });
    return response.data;
}

export async function loadCategories(client) {
    const response = await client.get('categories/');
    return response.data;
}

export async function loadCategory(path, client) {
    const response = await client.get(`categories/${path.join('/')}/`);
    return response.data;
}

export function loadProducts(page, pageSize, filters, ordering) {
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
    return fetch(url)
        .then(response => {
            if (!response.ok) throw response;
            return response.json();
        });
};

export async function getProductPrice(id, client) {
    const response = await client.get(`products/${id}/price/`);
    return response.data;
};

export async function checkUser(phone, reset) {
    const response = await apiClient.post('users/' + normalizePhone(phone) + '/check/', {
        reset
    });
    return response.data;
};

export async function loadPages(client) {
    const response = await client.get('pages/');
    return response.data;
}

export async function loadPage(uri, client) {
    const response = await client.get(`pages/${uri.join('/')}/`);
    return response.data;
}
