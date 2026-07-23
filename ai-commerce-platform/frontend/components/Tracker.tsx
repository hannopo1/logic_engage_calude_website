"use client";

import { usePathname } from "next/navigation";
import { useEffect } from "react";

import { api } from "@/lib/api";

/** Fires a page_view event on every route change. Mounted once in the layout. */
export default function Tracker() {
  const pathname = usePathname();
  useEffect(() => {
    // Don't count the operator console as storefront traffic.
    if (pathname.startsWith("/admin")) return;
    api.track({ event_type: "page_view", path: pathname });
  }, [pathname]);
  return null;
}
