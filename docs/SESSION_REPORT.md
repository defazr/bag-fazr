# bag.fazr.co.kr 세션 보고서

> 새 AI 세션(Claude/GPT)에서 컨텍스트 파악용

## 프로젝트 개요

종량제 봉투 판매처 찾기 서비스 (SEO 트래픽 기반)
- URL: https://bag.fazr.co.kr
- 동기: 2026 나프타 공급 위기 → 종량제 봉투 품귀

## 기술 스택

- Next.js 14 App Router + ISR (revalidate=86400)
- TailwindCSS v4
- Vercel 배포 + 가비아 도메인
- 정적 JSON 데이터 (런타임 API 호출 없음)
- Python 스크립트 (데이터 수집/분류)

## 프로젝트 구조

```
app/
  page.tsx              # 홈 (17개 시/도 그리드)
  [region]/page.tsx     # 시/도 페이지 (구별 그리드)
  [region]/[district]/page.tsx  # 구 페이지 (판매처 목록)
  sitemap.ts, robots.ts, not-found.tsx
lib/
  regions.ts            # 229개 district slug 매핑
  data.ts               # JSON 파일 리더
  seo.ts                # FAQ 생성, JSON-LD
  types.ts              # TypeScript 인터페이스
components/
  store/StoreCard.tsx, StoreList.tsx
  region/RegionGrid.tsx, DistrictGrid.tsx
  seo/Breadcrumb.tsx, FaqSection.tsx
  layout/Header.tsx, Footer.tsx
data/
  regions.json          # 전국 시/도 인덱스
  {region}/index.json   # 시/도별 구 인덱스
  {region}/{district}.json  # 구별 판매처 목록
  _unmatched.json       # 미분류 4건
scripts/
  collect.py            # API 수집 (주소 기반 분류)
  classify_all.py       # 최초 전국 분류 (구버전)
  reclassify_all.py     # 전체 재분류 (최신, 이것 사용)
```

## 데이터 현황 (2026-03-26)

- 전국 총: 69,615곳
- 17개 시/도, 229개 구/군/시
- 251 정적 페이지
- 미매칭: 4건 (무시 가능)
- API: 행정안전부_자원환경_쓰레기종량제봉투판매업
- API Key: 별도 관리 (collect.py --key 옵션)

## 핵심 기술 결정

1. **주소 파싱 기반 분류** (OPN_ATMY_GRP_CD 코드 사용 안 함)
2. **시/도 먼저 확정 → 그 안에서 구 매칭** (동명 구 오분류 방지)
3. **주소 normalize** 필수 (대전→대전광역시, 부산→부산광역시 등)
4. **세종 특수 처리** (구 없음 → 전부 sejongsi)
5. **0건 구 = soft 404 방지** (안내 페이지 + FAQ + 인접 링크)

## 완료된 SEO 최적화

- title: "[지역명] 종량제 봉투 파는곳 | 가격 | 크기 (2026 최신)"
- description: 판매처 수 + 가격 + 크기 + 편의점 언급
- FAQ 5개: 어디서/가격/크기/편의점/대란이유 (JSON-LD)
- 키워드 문장: "종량제 봉투는 지역별 가격과 크기가 다르며..."
- 내부링크: 인접 지역 + region 페이지 링크

## 0건 구 (API 데이터 없음)

서울: 강북구, 중랑구, 송파구
울산: 울주군
강원: 고성군
충남: 부여군, 청양군, 당진시

## 남은 작업

1. Google Search Console 등록 + sitemap 제출 (브라우저 수동)
2. Vercel 재배포 (SEO 최적화 반영)
3. 광고 연동 (AdSense)
4. 트래픽 키우기 전략
