import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AtlasTrip AI",
  description: "Autonomous travel planning with live agent telemetry, budgets, routes, and booking suggestions."
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
