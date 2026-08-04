import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/components/auth-provider";

export const metadata: Metadata = {
  title: "Orbit Work OS",
  description: "面向现代团队的 AI 工作操作系统",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body className="font-sans antialiased"><AuthProvider>{children}</AuthProvider></body>
    </html>
  );
}
