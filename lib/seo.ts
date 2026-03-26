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
      answer: `${regionName} ${districtName}에는 현재 ${count}곳의 종량제 봉투 판매처가 등록되어 있습니다. 편의점(GS25, CU, 세븐일레븐), 대형마트, 동네 슈퍼마켓 등에서 구매 가능합니다.`,
    },
    {
      question: `${districtName} 종량제 봉투 가격은 얼마인가요?`,
      answer: `종량제 봉투 가격은 지자체마다 다릅니다. ${districtName} 기준 일반 가정용 20L 봉투는 약 500~1,000원 수준이며, 정확한 가격은 판매처에서 확인하시기 바랍니다.`,
    },
    {
      question: `${districtName} 종량제 봉투 크기는 어떻게 되나요?`,
      answer: `종량제 봉투는 일반적으로 5L, 10L, 20L, 50L, 100L 등 다양한 크기로 판매됩니다. ${districtName}에서는 가정용 20L이 가장 많이 사용됩니다.`,
    },
    {
      question: `편의점에서도 종량제 봉투를 살 수 있나요?`,
      answer: `네, GS25, CU, 세븐일레븐 등 대부분의 편의점에서 종량제 봉투를 판매합니다. 다만 품귀 시에는 재고가 없을 수 있으니 미리 확인하세요.`,
    },
    {
      question: `종량제 봉투 대란 이유는 무엇인가요?`,
      answer: `2026년 중동 정세 불안으로 나프타 수급에 차질이 생기면서 종량제 봉투 원료(폴리에틸렌) 공급이 불안정해졌습니다. 일부 지역에서는 봉투 구매 수량이 제한되고 있습니다.`,
    },
  ];
}

export function getRegionFaqs(regionName: string, districtCount: number) {
  return [
    {
      question: `${regionName} 종량제 봉투 어디서 사나요?`,
      answer: `${regionName}에는 ${districtCount}개 시/군/구에서 종량제 봉투를 판매하고 있습니다. 편의점, 마트, 슈퍼마켓 등에서 구매 가능하며, 각 지역 페이지에서 상세 판매처를 확인하세요.`,
    },
    {
      question: `${regionName} 종량제 봉투 가격은 얼마인가요?`,
      answer: `종량제 봉투 가격은 지자체별로 다릅니다. 일반 가정용 20L 기준 약 500~1,000원 수준이며, 정확한 가격은 해당 시/군/구 판매처에서 확인하세요.`,
    },
    {
      question: `종량제 봉투 대란 이유는 무엇인가요?`,
      answer: `2026년 중동 정세 불안으로 나프타 수급에 차질이 생기면서 종량제 봉투 원료 공급이 불안정해졌습니다. 일부 지역에서는 구매 수량이 제한되고 있습니다.`,
    },
    {
      question: `편의점에서도 종량제 봉투를 살 수 있나요?`,
      answer: `네, GS25, CU, 세븐일레븐 등 대부분의 편의점에서 종량제 봉투를 판매합니다. 다만 품귀 시에는 재고가 없을 수 있습니다.`,
    },
  ];
}
