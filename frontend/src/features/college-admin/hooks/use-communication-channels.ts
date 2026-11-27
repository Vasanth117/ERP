"use client";

import { useMemo } from "react";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import {
  fetchCommunicationEmailChannelPage,
  fetchCommunicationSmsChannelPage,
  fetchCommunicationWhatsappChannelPage,
} from "@/features/college-admin/api/communication-channels";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useCommunicationEmailChannelPage(params?: { page?: number; page_size?: number }, enabled = true) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.communicationEmailChannelPage(params),
    queryFn: () => fetchCommunicationEmailChannelPage(params),
    enabled,
  });
}

export function useCommunicationSmsChannelPage(params?: { page?: number; page_size?: number }, enabled = true) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.communicationSmsChannelPage(params),
    queryFn: () => fetchCommunicationSmsChannelPage(params),
    enabled,
  });
}

export function useCommunicationWhatsappChannelPage(params?: { page?: number; page_size?: number }, enabled = true) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.communicationWhatsappChannelPage(params),
    queryFn: () => fetchCommunicationWhatsappChannelPage(params),
    enabled,
  });
}

export function useCommunicationChannelPage(
  variant: "email" | "sms" | "whatsapp",
  page: number,
  pageSize = 3,
) {
  const params = useMemo(() => ({ page, page_size: pageSize }), [page, pageSize]);
  const email = useCommunicationEmailChannelPage(params, variant === "email");
  const sms = useCommunicationSmsChannelPage(params, variant === "sms");
  const whatsapp = useCommunicationWhatsappChannelPage(params, variant === "whatsapp");
  if (variant === "sms") return sms;
  if (variant === "whatsapp") return whatsapp;
  return email;
}