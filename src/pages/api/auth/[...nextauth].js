import NextAuth from 'next-auth';
import CredentialsProvider from "next-auth/providers/credentials";

import jwt from "jsonwebtoken"

import { API, apiClient } from '@/lib/queries';

async function refreshAccessToken(token) {
    try {
        // Get a new set of tokens
        const response = await apiClient.post(API + 'token/refresh/', {refresh: token.sjwt.refresh});
        console.error(response.data);

        const accessToken = jwt.verify(response.data.sjwt.access, process.env.NEXTAUTH_SECRET);

        token = {
            ...token,
            ...response.data,
            sjwt: {
                //expires: new Date(accessToken.exp * 1000),
                refresh: sjwt.refresh ?? token.sjwt.refresh // Fall back to old refresh token
            },
            error: undefined
        }
        console.log(token);
        return token;
    } catch (error) {
        console.error(error);
        return {
            ...token,
            error: "RefreshAccessTokenError",
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

                if (!response.data.user)
                    throw JSON.stringify(response);

                // TODO: Do we need this?
                const accessToken = jwt.verify(response.data.sjwt.access, process.env.NEXTAUTH_SECRET);

                return response.data;
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
                ...user
            }
        }

        // Return previous token if the access token has not expired yet
        if (Math.floor(Date.now() / 1000) < token.sjwt.accessExpires) {
            return token;
        }

        // Access token has expired, try to update it
        return refreshAccessToken(token);
    },
    session: async ({ session, token }) => {
        session = {
            ...session,
            ...token,
        };
        // Pass accessToken to the client to be used in authentication with your API
        session.accessToken = token.sjwt.access;
        session.accessTokenExpires = token.sjwt.accessExpires;
        session.error = token.error;
        // Remove internal data
        delete session.sjwt;

        return session;
    },
}

export const options = {
    providers,
    callbacks,
    debug: true
}

export default NextAuth(options);
