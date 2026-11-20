"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { usePathname } from "next/navigation";
import { useState, type ReactNode } from "react";

import { AuthSessionBootstrap } from "@/components/auth/auth-session-bootstrap";
import { Toaster } from "@/components/ui/sonner";

type AppProvidersProps = {
  children: ReactNode;
};

export function AppProviders({ children }: AppProvidersProps) {
  const pathname = usePathname();
  const isFullViewportRoute =
    pathname === "/" ||
    pathname?.startsWith("/under-construction") ||
    pathname?.startsWith("/college-admin");
  const showQueryDevtools =
    process.env.NODE_ENV === "development" && !isFullViewportRoute;

  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            refetchOnWindowFocus: false,
            retry: 1,
          },
        },
      }),
  );

  return (
    <QueryClientProvider client={queryClient}>
      <AuthSessionBootstrap />
      {children}
      <Toaster richColors closeButton position="top-right" />
      {showQueryDevtools ? (
        <ReactQueryDevtools initialIsOpen={false} buttonPosition="bottom-left" />
      ) : null}
    </QueryClientProvider>
  );
}