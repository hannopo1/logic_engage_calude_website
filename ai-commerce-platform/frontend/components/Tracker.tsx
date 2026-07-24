"use client";

import { usePathname } from "next/navigation";
import { useEffect } from "react";

import { api } from "@/lib/api";

/**
 * Tracks storefront page views when the route changes.
 *
 * Administrative routes are excluded from tracking. Mount this component once in the application layout.
 */
export default function Tracker() {
  const pathname = usePathname();
  useEffect(() => {
    // Don't count the operator console as storefront traffic.
    if (pathname.startsWith("/admin")) return;
    api.track({ event_type: "page_view", path: pathname });
  }, [pathname]);
  return null;
}
