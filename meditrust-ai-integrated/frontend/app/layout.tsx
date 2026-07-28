import type { Metadata } from "next";
import { Rubik, Space_Grotesk, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { CinematicHeader } from "@/components/shell/CinematicHeader";
import { Footer } from "@/components/shell/Footer";

const rubik = Rubik({
  variable: "--font-rubik",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const spaceGrotesk = Space_Grotesk({
  variable: "--font-display",
  subsets: ["latin"],
  weight: ["500", "600", "700"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-code",
  subsets: ["latin"],
  weight: ["400", "500", "700"],
});

export const metadata: Metadata = {
  title: "MediTrust AI | Governed Healthcare Knowledge Assistant",
  description:
    "Grounded healthcare knowledge experience providing trusted evidence and concise citation-backed summaries.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${rubik.variable} ${spaceGrotesk.variable} ${jetbrainsMono.variable} h-full antialiased`}
    >
      <body className="min-h-screen flex flex-col bg-[#f7f6fa] text-[#1f1633] font-sans selection:bg-[#c2ef4e]/30 selection:text-[#1f1633]">
        <CinematicHeader />
        <div className="flex-1 flex flex-col">{children}</div>
        <Footer />
      </body>
    </html>
  );
}
