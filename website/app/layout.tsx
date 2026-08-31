import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Majestic AI Fisher",
  description: "Desktop automation workspace and account portal",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="ru"><body>{children}</body></html>;
}
