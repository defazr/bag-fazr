import type { Metadata } from "next";
import Script from "next/script";
import "./globals.css";
import Header from "@/components/layout/Header";
import Footer from "@/components/layout/Footer";
import NoticeBanner from "@/components/layout/NoticeBanner";
import ScrollToTop from "@/components/layout/ScrollToTop";
import StickyBottomAd from "@/components/ads/StickyBottomAd";

export const metadata: Metadata = {
  metadataBase: new URL("https://bag.fazr.co.kr"),
  openGraph: {
    title: "종량제 봉투 판매처 찾기",
    description: "전국 종량제 봉투 판매처를 지역별로 확인하세요",
    url: "https://bag.fazr.co.kr",
    siteName: "bag.fazr",
    images: [
      {
        url: "/og-default.jpg",
        width: 1200,
        height: 630,
      },
    ],
    locale: "ko_KR",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "종량제 봉투 판매처 찾기",
    description: "전국 판매처 6만+ 데이터 제공",
    images: ["/og-default.jpg"],
  },
  icons: {
    icon: "/favicon.ico",
    apple: "/apple-touch-icon.png",
  },
  verification: {
    other: {
      "naver-site-verification": "280cd143ab2dd3a365ed74ace4482326ec8e9474",
    },
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body className="min-h-screen bg-gray-50 text-gray-900 antialiased dark:bg-zinc-950 dark:text-zinc-400">
        <Script
          async
          src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-7976139023602789"
          crossOrigin="anonymous"
          strategy="afterInteractive"
        />
        <NoticeBanner />
        <Header />
        <main className="mx-auto max-w-4xl px-4 py-8">{children}</main>
        <Footer />
        <ScrollToTop />
        <StickyBottomAd />
      </body>
    </html>
  );
}
