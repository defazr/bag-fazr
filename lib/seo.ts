const SITE_URL = "https://bag.fazr.co.kr";
const SITE_NAME = "종량제 봉투 판매처 찾기";

export function getBaseUrl() {
  return SITE_URL;
}

export function getSiteName() {
  return SITE_NAME;
}

export function generateFaqSchema(
  faqs: { question: string; answer: string }[]
) {
  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: faqs.map((faq) => ({
      "@type": "Question",
      name: faq.question,
      acceptedAnswer: {
        "@type": "Answer",
        text: faq.answer,
      },
    })),
  };
}

export function getDistrictFaqs(
  regionName: string,
  districtName: string,
  count: number
) {
  return [
    {
      question: `${districtName} 종량제 봉투 어디서 사나요?`,
      answer: `${regionName} ${districtName}에는 현재 ${count}곳의 종량제 봉투 판매처가 등록되어 있습니다. 편의점, 마트, 슈퍼마켓 등에서 구매 가능합니다.`,
    },
    {
      question: `종량제 봉투가 품귀인 이유는?`,
      answer: `2026년 3월 기준 중동 정세 불안으로 나프타 수급에 차질이 생기면서 종량제 봉투 원료 공급이 불안정해졌습니다.`,
    },
    {
      question: `${districtName} 종량제 봉투 가격은 얼마인가요?`,
      answer: `종량제 봉투 가격은 지자체마다 다릅니다. ${districtName}의 정확한 가격은 해당 판매처에 문의하시기 바랍니다.`,
    },
  ];
}

export function getRegionFaqs(regionName: string, districtCount: number) {
  return [
    {
      question: `${regionName} 종량제 봉투 어디서 사나요?`,
      answer: `${regionName}에는 ${districtCount}개 시/군/구에서 종량제 봉투를 판매하고 있습니다. 각 지역 페이지에서 상세 판매처를 확인하세요.`,
    },
    {
      question: `종량제 봉투 품귀 현상은 언제까지 계속되나요?`,
      answer: `중동 정세와 나프타 수급 상황에 따라 달라질 수 있습니다. 최신 현황은 뉴스를 참고해주세요.`,
    },
  ];
}
