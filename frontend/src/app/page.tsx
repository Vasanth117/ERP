import type { Metadata } from "next";
import { Inter } from "next/font/google";

import { LandingPage } from "@/features/landing/components/landing-page";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-landing",
  display: "swap",
});

export const metadata: Metadata = {
  title: "College ERP — Select an Entry Point",
  description:
    "Choose an ERP module workspace. Main landing page from Figma (Main Landing Page / Select an Entry Point).",
};

export default function HomePage() {
  return (
    <div className={inter.className}>
      <LandingPage />
    </div>
  );
}