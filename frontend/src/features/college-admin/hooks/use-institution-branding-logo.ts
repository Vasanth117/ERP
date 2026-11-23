"use client";

import { useEffect, useRef, useState } from "react";

import { fetchInstitutionBrandingFile } from "@/features/college-admin/api/institution";

/** Loads a tenant branding image via authenticated fetch (for use in `<img>`). */
export function useInstitutionBrandingLogoUrl(fileId: string | null | undefined): string | null {
  const [url, setUrl] = useState<string | null>(null);
  const objectUrlRef = useRef<string | null>(null);

  useEffect(() => {
    if (!fileId) {
      if (objectUrlRef.current) {
        URL.revokeObjectURL(objectUrlRef.current);
        objectUrlRef.current = null;
      }
      setUrl(null);
      return;
    }

    let active = true;

    void fetchInstitutionBrandingFile(fileId)
      .then((blob) => {
        if (!active) return;
        if (objectUrlRef.current) {
          URL.revokeObjectURL(objectUrlRef.current);
        }
        const next = URL.createObjectURL(blob);
        objectUrlRef.current = next;
        setUrl(next);
      })
      .catch(() => {
        if (active) setUrl(null);
      });

    return () => {
      active = false;
      if (objectUrlRef.current) {
        URL.revokeObjectURL(objectUrlRef.current);
        objectUrlRef.current = null;
      }
    };
  }, [fileId]);

  return url;
}