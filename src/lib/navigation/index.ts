/*
Temporary provider that supports both app and pages routers.
TODO: Remove after full switch to apps router.
*/

"use client";

import { createContext, useContext } from "react";
import { ParsedUrlQuery } from "querystring";
import { RouterEvent } from "next/router";
import { MittEmitter } from "next/dist/shared/lib/mitt";

export type NavigateOptions = {
  replace?: boolean;
  scroll?: boolean;
};

export type NavigationContextValue = {
  path: string;
  query: ParsedUrlQuery;
  navigate: (href: string, options?: NavigateOptions) => void;
  back: () => void;
  forward: () => void;
  refresh: () => void;
  events?: MittEmitter<RouterEvent>
};

export const NavigationContext =
  createContext<NavigationContextValue | null>(null);

export function useNavigation() {
  const context = useContext(NavigationContext);

  if (!context) {
    throw new Error(
      "useNavigation must be used within <AppNavigationProvider> or <PagesNavigationProvider>"
    );
  }

  return context;
}