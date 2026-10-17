"use client";

import { useCallback, useMemo, type ReactNode } from "react";
import { usePathname, useRouter, useSearchParams, ReadonlyURLSearchParams } from "next/navigation";
import { ParsedUrlQuery } from 'querystring';
import { NavigationContext, type NavigateOptions, type NavigationContextValue } from ".";


export function convertSearchParams(searchParams: ReadonlyURLSearchParams | null): ParsedUrlQuery {
  const query: ParsedUrlQuery = {};

  if (searchParams === null)
    return query;

  searchParams.forEach((value, key) => {
    const existing = query[key];

    if (existing !== undefined) {
      // If the key already exists, turn it into an array or push to it
      query[key] = Array.isArray(existing) ? [...existing, value] : [existing, value];
    } else {
      query[key] = value;
    }
  });

  return query;
}

export function AppNavigationProvider({
  children,
}: {
  children: ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname() ?? '';
  const searchParams = useSearchParams();
  const query = useMemo(() => convertSearchParams(searchParams), [searchParams])

  const queryString = searchParams?.toString();
  const path = queryString ? `${pathname}?${queryString}` : pathname;

  const navigate = useCallback(
    (href: string, options: NavigateOptions = {}) => {
      const { replace = false, scroll } = options;

      if (replace) {
        router.replace(href, { scroll });
      } else {
        router.push(href, { scroll });
      }
    },
    [router]
  );

  const value = useMemo<NavigationContextValue>(
    () => ({
      path,
      query,
      navigate,
      back: () => router.back(),
      forward: () => router.forward(),
      refresh: () => router.refresh(),
    }),
    [navigate, path, query, router]
  );

  return (
    <NavigationContext.Provider value={value}>
      {children}
    </NavigationContext.Provider>
  );
}