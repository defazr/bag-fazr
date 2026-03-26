import type { Metadata } from "next";
// import Script from "next/script";
import "./globals.css";
import Header from "@/components/layout/Header";
import Footer from "@/components/layout/Footer";
import NoticeBanner from "@/components/layout/NoticeBanner";
// import StickyBottomAd from "@/components/ads/StickyBottomAd";

export const metadata: Metadata = {
  metadataBase: new URL("https://bag.fazr.co.kr"),
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body className="min-h-screen bg-gray-50 text-gray-900 antialiased pb-14 sm:pb-0">
        {/* <Script
          async
          src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-7976139023602789"
          crossOrigin="anonymous"
          strategy="afterInteractive"
        /> */}
        <NoticeBanner />
        <Header />
        <main className="mx-auto max-w-4xl px-4 py-8">{children}</main>
        <Footer />
        {/* <StickyBottomAd /> */}
      </body>
    </html>
  );
}
