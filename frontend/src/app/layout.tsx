import "./globals.css";
import Providers from "./providers";
import { Toaster } from "sonner";
import TopNav from "@/components/top-nav";

export const metadata = { title: "SentinelX", description: "SOC console" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-neutral-50 text-neutral-900">
        <Providers>
          <TopNav />
          <main className="mx-auto max-w-7xl">{children}</main>
        </Providers>
        <Toaster richColors position="top-right" />
      </body>
    </html>
  );
}