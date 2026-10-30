"use client";

import { useCallback, useMemo, type ReactNode } from "react";
import { useRouter } from "next/router";
import { NavigationContext, type NavigateOptions, type NavigationContextValue } from ".";

export function PagesNavigationProvider({
  children,
}: {
  children: ReactNode;
}) {
  const router = useRouter();

  const navigate = useCallback(
    (href: string, options: NavigateOptions = {}) => {
      const { replace = false } = options;

      if (replace) {
        router.replace(href);
      } else {
        router.push(href);
      }
    },
    [router]
  );

  const value = useMemo<NavigationContextValue>(
    () => ({
      path: router.asPath,
      query: router.query,
      navigate,
      back: () => router.back(),
      forward: () => router.forward(),
      refresh: () => router.reload(),
      events: router.events,
    }),
    [navigate, router]
  );

  return (
    <NavigationContext.Provider value={value}>
      {children}
    </NavigationContext.Provider>
  );
}