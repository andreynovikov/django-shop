import NextAuth from 'next-auth';
import CredentialsProvider from "next-auth/providers/credentials";

import jwt from "jsonwebtoken"

import { API, apiClient } from '@/lib/queries';

async function refreshAccessToken(token) {
    try {
        console.error("refreshAccessToken");
        // Get a new set of tokens
        const response = await apiClient.post(API + 'token/refresh/', {refresh: token.sjwt.refresh});

        const accessToken = jwt.verify(response.data.access, process.env.NEXTAUTH_SECRET);  // TODO: check for error

        token = {
            ...token,
            sjwt: {
                ...token.sjwt,
                ...response.data,
                expires: accessToken.exp,
            },
            error: undefined
        }
        console.log(token);
        return token;
    } catch (error) {
        console.error(error);
        return {
            ...token,
            error: "RefreshAccessTokenError"
        }
    }
}

const providers = [
    CredentialsProvider({
        name: 'Credentials',
        credentials: {
            phone: { label: "Phone", type: "text", placeholder: "+79991234567" },
            password: {  label: "Password", type: "password" }
        },
        authorize: async (credentials) => {
            try {
                // Authenticate user with credentials
                const response = await apiClient.post(API + 'users/login/', credentials);
                console.error(response.data);

                const accessToken = jwt.verify(response.data.access, process.env.NEXTAUTH_SECRET); // TODO: check for error

                if (!response.data.id) // TODO: process error correctly
                    throw response;

                return {
                    ...response.data,
                    expires: accessToken.exp
                }
            } catch (e) {
                if (e.response) {
                    // The client was given an error response (5xx, 4xx)
                    console.log(e.response.data);
                    console.log(e.response.status);
                    console.log(e.response.headers);
                } else if (e.request) {
                    // The client never received a response, and the request was never left
                    console.error(e.request);
                } else {
                    // Anything else
                    console.error(e);
                }
                throw new Error(e);
            }
        }
    })
]

const callbacks = {
    jwt: async ({ token, user }) => {
        // Initial sign in
        if (user) {
            return {
                ...token,
                sjwt: user
            }
        }

        // Return previous token if the access token has not expired yet
        if (Math.floor(Date.now() / 1000) < token.sjwt.expires) {
            return token;
        }

        // Access token has expired, try to update it
        return refreshAccessToken(token);
    },
    session: async ({ session, token }) => {
        // Pass accessToken to the client to be used in authentication with API
        session = {
            ...session,
            user: token.sjwt.id,
            accessToken: token.sjwt.access,
            accessTokenExpires: token.sjwt.expires,
            error: token.error
        };
        return session;
    },
}

export const options = {
    providers,
    callbacks,
    debug: true,
    pages: {
        signIn: '/login'
    },
    session: {
        maxAge: 60 * 60 // must be synced to DRF JWT settings
    }
}

export default NextAuth(options);
