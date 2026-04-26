import type { Metadata } from "next";
import Link from "next/link";
import Breadcrumb from "@/components/seo/Breadcrumb";
import FaqSection from "@/components/seo/FaqSection";
import RegionLinks from "@/components/article/RegionLinks";

export const metadata: Metadata = {
  title: "쓰레기봉투 파는곳 총정리 | 종량제봉투 판매처 찾기 (2026)",
  description:
    "쓰레기봉투 파는곳 찾고 계신가요? 전국 69,000곳 이상의 종량제봉투 판매처를 지역별로 정리했습니다. 편의점, 마트, 슈퍼 등 내 주변 판매처를 바로 확인하세요.",
  alternates: {
    canonical: "https://bag.fazr.co.kr/article/where-to-buy",
  },
  openGraph: {
    title: "쓰레기봉투 파는곳 총정리 (2026)",
    description: "전국 종량제봉투 판매처를 지역별로 한 번에 확인하세요",
  },
};

export default function WhereToBuyPage() {
  const faqs = [
    {
      question: "종량제봉투는 어디서 살 수 있나요?",
      answer:
        "편의점(CU, GS25, 세븐일레븐), 동네 슈퍼, 대형마트, 주민센터 등에서 구매할 수 있습니다. 전국 69,000곳 이상의 판매처를 지역별로 확인할 수 있습니다.",
    },
    {
      question: "편의점에서 종량제봉투가 품절이면 어떻게 하나요?",
      answer:
        "편의점보다 동네 슈퍼나 대형마트에 재고가 남아있는 경우가 많습니다. 판매처 목록을 확인하고 방문하면 헛걸음을 줄일 수 있습니다.",
    },
    {
      question: "다른 지역 종량제봉투를 사용할 수 있나요?",
      answer:
        "정책상 전국 호환이 가능하도록 변경되었으나, 지자체별 시행 시점이 다릅니다. 해당 구청에 확인이 필요합니다.",
    },
    {
      question: "종량제봉투 가격은 얼마인가요?",
      answer:
        "지역과 사이즈(10L, 20L, 50L, 100L 등)에 따라 가격이 다릅니다. 정확한 가격은 해당 지역 판매처에서 확인하는 것이 가장 정확합니다.",
    },
  ];

  return (
    <>
      <Breadcrumb items={[{ label: "쓰레기봉투 파는곳 총정리" }]} />

      <article>
        <header className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white leading-tight">
            쓰레기봉투 파는곳 총정리 | 종량제봉투 판매처 찾기 (2026)
          </h1>
          <p className="mt-2 text-sm text-gray-500 dark:text-zinc-500">
            2026년 4월 업데이트
          </p>
        </header>

        <div className="space-y-6 text-[15px] text-gray-700 dark:text-zinc-300 leading-relaxed">
          {/* 즉시 클릭 영역 */}
          <p className="text-sm">
            내 주변 판매처 바로 확인:{" "}
            <Link href="/seoul" className="font-medium underline underline-offset-2 hover:text-gray-900 dark:hover:text-white transition">서울</Link>
            {" / "}
            <Link href="/gyeonggi" className="font-medium underline underline-offset-2 hover:text-gray-900 dark:hover:text-white transition">경기</Link>
            {" / "}
            <Link href="/busan" className="font-medium underline underline-offset-2 hover:text-gray-900 dark:hover:text-white transition">부산</Link>
          </p>

          {/* 섹션 1: 도입부 */}
          <section>
            <h2 className="text-lg font-bold text-gray-900 dark:text-white border-l-4 border-orange-400 pl-3 mt-10 mb-4">
              쓰레기봉투 어디서 사야 하나
            </h2>
            <p>
              쓰레기봉투 파는곳 찾고 계신가요? 종량제봉투 파는곳을 지역별로 한 번에 확인할 수 있도록 정리했습니다.
            </p>
            <p className="mt-3">
              편의점에 갔는데 품절. 옆 마트에 가도 품절. 2026년 들어서 이런 경험을 한 사람이 급격히 늘었습니다. 봉투가 아예 없는 게 아니라, 어디에 남아있는지 모르는 게 문제입니다.
            </p>
            <p className="mt-3">
              전국 69,000곳 이상의 종량제봉투 판매처를 지역별로 정리해뒀습니다. 발품 팔기 전에 먼저 확인하세요. 왜 봉투가 부족한 건지 궁금하다면{" "}
              <Link href="/article/shortage-2026" className="font-medium underline underline-offset-2 hover:text-gray-900 dark:hover:text-white transition">2026 종량제 봉투 대란 이유</Link>
              를 함께 보시면 도움이 됩니다.
            </p>
          </section>

          {/* 섹션 2: 지역별 판매처 바로가기 (허브) */}
          <section>
            <h2 className="text-lg font-bold text-gray-900 dark:text-white border-l-4 border-orange-400 pl-3 mt-10 mb-4">
              지역별 판매처 바로가기
            </h2>
            <p>
              내 지역의 판매처를 클릭해서 바로 확인하세요.
            </p>
            <ul className="mt-3 space-y-3">
              <li>
                <Link href="/seoul" className="font-medium underline underline-offset-2 hover:text-gray-900 dark:hover:text-white transition"><strong className="text-gray-900 dark:text-white">서울 종량제봉투 판매처 확인</strong></Link>
                <span className="ml-1">— 강남, 서초, 송파 등 25개 구별 판매처</span>
              </li>
              <li>
                <Link href="/gyeonggi" className="font-medium underline underline-offset-2 hover:text-gray-900 dark:hover:text-white transition"><strong className="text-gray-900 dark:text-white">경기 종량제봉투 파는곳</strong></Link>
                <span className="ml-1">— 수원, 성남, 용인, 고양 등 경기도 전역</span>
              </li>
              <li>
                <Link href="/busan" className="font-medium underline underline-offset-2 hover:text-gray-900 dark:hover:text-white transition"><strong className="text-gray-900 dark:text-white">부산 쓰레기봉투 구매처</strong></Link>
                <span className="ml-1">— 해운대, 사하, 북구 등</span>
              </li>
              <li>
                <Link href="/daegu" className="font-medium underline underline-offset-2 hover:text-gray-900 dark:hover:text-white transition"><strong className="text-gray-900 dark:text-white">대구</strong></Link>
                <span className="ml-1">— 달서, 북구, 수성 등</span>
              </li>
              <li>
                <Link href="/incheon" className="font-medium underline underline-offset-2 hover:text-gray-900 dark:hover:text-white transition"><strong className="text-gray-900 dark:text-white">인천</strong></Link>
                <span className="ml-1">— 남동, 부평, 서구 등</span>
              </li>
              <li>
                <Link href="/ulsan" className="font-medium underline underline-offset-2 hover:text-gray-900 dark:hover:text-white transition"><strong className="text-gray-900 dark:text-white">울산</strong></Link>
                <span className="ml-1">— 남구, 중구, 북구 등</span>
              </li>
            </ul>
            <p className="mt-3">
              그 외 지역:{" "}
              <Link href="/daejeon" className="font-medium underline underline-offset-2 hover:text-gray-900 dark:hover:text-white transition">대전</Link>
              {" / "}
              <Link href="/gwangju" className="font-medium underline underline-offset-2 hover:text-gray-900 dark:hover:text-white transition">광주</Link>
              {" / "}
              <Link href="/sejong" className="font-medium underline underline-offset-2 hover:text-gray-900 dark:hover:text-white transition">세종</Link>
              {" / "}
              <Link href="/gangwon" className="font-medium underline underline-offset-2 hover:text-gray-900 dark:hover:text-white transition">강원</Link>
              {" / "}
              <Link href="/chungbuk" className="font-medium underline underline-offset-2 hover:text-gray-900 dark:hover:text-white transition">충북</Link>
              {" / "}
              <Link href="/chungnam" className="font-medium underline underline-offset-2 hover:text-gray-900 dark:hover:text-white transition">충남</Link>
              {" / "}
              <Link href="/jeonbuk" className="font-medium underline underline-offset-2 hover:text-gray-900 dark:hover:text-white transition">전북</Link>
              {" / "}
              <Link href="/jeonnam" className="font-medium underline underline-offset-2 hover:text-gray-900 dark:hover:text-white transition">전남</Link>
              {" / "}
              <Link href="/gyeongbuk" className="font-medium underline underline-offset-2 hover:text-gray-900 dark:hover:text-white transition">경북</Link>
              {" / "}
              <Link href="/gyeongnam" className="font-medium underline underline-offset-2 hover:text-gray-900 dark:hover:text-white transition">경남</Link>
              {" / "}
              <Link href="/jeju" className="font-medium underline underline-offset-2 hover:text-gray-900 dark:hover:text-white transition">제주</Link>
            </p>
          </section>

          {/* CTA 중간 */}
          <p className="text-sm mb-2 text-gray-600 dark:text-zinc-400">
            쓰레기봉투 파는곳을 지역별로 확인할 수 있습니다
          </p>
          <div className="rounded-xl border border-gray-200 dark:border-zinc-700 bg-gray-50 dark:bg-zinc-800 p-6 text-center shadow-sm">
            <p className="font-bold text-gray-900 dark:text-white">
              내 주변 판매처, 지금 바로 확인하세요
            </p>
            <p className="mt-1 text-sm text-gray-500 dark:text-zinc-400">
              전국 69,000곳 이상의 판매처를 지역별로 검색할 수 있습니다
            </p>
            <Link
              href="/"
              className="mt-4 inline-block rounded-xl bg-gray-900 dark:bg-zinc-700 px-6 py-2.5 text-sm font-medium text-white hover:bg-gray-800 dark:hover:bg-zinc-600 transition"
            >
              내 주변 판매처 바로 찾기 →
            </Link>
          </div>

          {/* 섹션 3: 파는 곳 종류 */}
          <section>
            <h2 className="text-lg font-bold text-gray-900 dark:text-white border-l-4 border-orange-400 pl-3 mt-10 mb-4">
              종량제봉투 파는 곳 종류
            </h2>
            <p>
              종량제봉투를 구매할 수 있는 곳은 크게 5가지입니다.
            </p>
            <ul className="mt-3 space-y-3">
              <li>
                <strong className="text-gray-900 dark:text-white">편의점</strong>
                <span className="ml-1">— CU, GS25, 세븐일레븐 등. 가장 접근성이 높지만 2026년 현재 재고가 가장 빠르게 소진됩니다.</span>
              </li>
              <li>
                <strong className="text-gray-900 dark:text-white">동네 슈퍼/마트</strong>
                <span className="ml-1">— 편의점보다 재고가 오래 유지되는 경우가 많습니다. 의외로 가장 확실한 구매처입니다.</span>
              </li>
              <li>
                <strong className="text-gray-900 dark:text-white">대형마트</strong>
                <span className="ml-1">— 이마트, 홈플러스, 롯데마트 등. 물량은 크지만 인기 사이즈는 빠르게 소진됩니다.</span>
              </li>
              <li>
                <strong className="text-gray-900 dark:text-white">주민센터/행정복지센터</strong>
                <span className="ml-1">— 일부 지역에서 직접 판매합니다.</span>
              </li>
              <li>
                <strong className="text-gray-900 dark:text-white">온라인 구매</strong>
                <span className="ml-1">— 종량제닷컴 등에서 배송 구매가 가능합니다. 급하지 않다면 편리한 방법입니다.</span>
              </li>
            </ul>
          </section>

          {/* 섹션 4: 편의점 종량제봉투 */}
          <section>
            <h2 className="text-lg font-bold text-gray-900 dark:text-white border-l-4 border-orange-400 pl-3 mt-10 mb-4">
              편의점에서 종량제봉투 살 수 있나요
            </h2>
            <p>
              CU, GS25, 세븐일레븐 등 편의점에서도 종량제봉투를 판매합니다. 다만 지역과 매장에 따라 재고가 없는 경우가 많습니다.
            </p>
            <p className="mt-3">
              편의점 종량제봉투가 품절이라면 동네 슈퍼를 먼저 확인해보세요. 편의점은 진열 공간이 작아서 소진이 빠르지만, 슈퍼는 의외로 재고가 남아있는 경우가 많습니다.
            </p>
          </section>

          {/* 섹션 5: 가격 / 사이즈 */}
          <section>
            <h2 className="text-lg font-bold text-gray-900 dark:text-white border-l-4 border-orange-400 pl-3 mt-10 mb-4">
              종량제봉투 가격과 사이즈
            </h2>
            <p>
              종량제봉투 가격과 사이즈는 지역마다 다릅니다. 10L, 20L, 50L, 100L 등 크기별로 가격이 다르기 때문에 정확한 가격은 해당 지역 판매처에서 확인하는 것이 가장 정확합니다.
            </p>
            <p className="mt-3">
              같은 사이즈라도 시/군/구마다 단가가 다르고, 같은 지역 안에서도 매장마다 가격이 다를 수 있습니다.
            </p>
          </section>

          {/* 섹션 6: 봉투 구매 팁 */}
          <section>
            <h2 className="text-lg font-bold text-gray-900 dark:text-white border-l-4 border-orange-400 pl-3 mt-10 mb-4">
              봉투 구매할 때 알아두면 좋은 점
            </h2>
            <p>
              타 지역 종량제봉투 사용에 대해서는 2024년에 전국 호환 정책이 발표되었으나, 지자체별 시행 시점이 다릅니다. 해당 구청에 확인이 필요합니다.
            </p>
            <p className="mt-3">
              사재기는 자제해주세요. 생산은 계속되고 있고, 일시적인 수급 불균형입니다. 직접 겪어본 후기가 궁금하다면{" "}
              <Link href="/article/why-no-bags" className="font-medium underline underline-offset-2 hover:text-gray-900 dark:hover:text-white transition">종량제 봉투 요즘 왜 없을까</Link>
              를 함께 읽어보세요.
            </p>
          </section>

          {/* CTA 하단 */}
          <div className="rounded-xl border border-gray-200 dark:border-zinc-700 bg-gray-50 dark:bg-zinc-800 p-6 text-center shadow-sm">
            <p className="font-bold text-gray-900 dark:text-white">
              종량제 봉투 판매처, 지금 바로 확인하세요
            </p>
            <p className="mt-1 text-sm text-gray-500 dark:text-zinc-400">
              지역을 선택하면 가까운 판매처 목록을 바로 볼 수 있습니다
            </p>
            <Link
              href="/"
              className="mt-4 inline-block rounded-xl bg-gray-900 dark:bg-zinc-700 px-6 py-2.5 text-sm font-medium text-white hover:bg-gray-800 dark:hover:bg-zinc-600 transition"
            >
              내 주변 판매처 바로 찾기 →
            </Link>
          </div>

          <RegionLinks />

          {/* 섹션 7: 정리 */}
          <section>
            <h2 className="text-lg font-bold text-gray-900 dark:text-white border-l-4 border-orange-400 pl-3 mt-10 mb-4">
              정리
            </h2>
            <p>
              종량제봉투는 없어진 게 아니라 어디 있는지 모를 뿐입니다. 미리 확인하고 가면 헛걸음을 줄일 수 있습니다.
            </p>
          </section>
        </div>
      </article>

      <FaqSection faqs={faqs} />

      {/* 신뢰 시그널 */}
      <div className="mt-10 rounded-xl bg-gray-50 dark:bg-zinc-900 px-5 py-3 text-xs text-gray-400 dark:text-zinc-500">
        본 페이지는 공공데이터를 기반으로 정리한 정보 페이지입니다. 실시간 재고는 매장에 따라 다를 수 있습니다.
      </div>
    </>
  );
}
