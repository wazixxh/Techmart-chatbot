import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Techmart Chatbot",
  description: "AI Assistant for Techmart",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased min-h-screen bg-slate-950 text-slate-50">
        {children}
      </body>
    </html>
  );
}
