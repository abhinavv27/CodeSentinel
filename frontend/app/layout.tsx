import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const jetbrains = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono" });

export const metadata: Metadata = {
  title: "CodeSentinel — Automated Code Review",
  description:
    "LLM-powered automated PR code reviewer. Flags anti-patterns, security issues, and bugs in under 45 seconds.",
  keywords: ["code review", "AI code review", "LLM", "automated PR review", "security audit", "Qdrant RAG"],
  authors: [{ name: "Abhinav" }],
  openGraph: {
    title: "CodeSentinel",
    description: "AI-Powered Code Review Agent",
    type: "website",
  }
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrains.variable}`}>
      <body className="antialiased">{children}</body>
    </html>
  );
}

