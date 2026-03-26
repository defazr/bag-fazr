# bag.fazr.co.kr GPT 세션 보고서

> GPT 새 세션에서 컨텍스트 파악용. 이 파일을 GPT에 첨부하세요.

## 프로젝트 한 줄 요약

종량제 봉투 판매처 찾기 서비스. SEO 트래픽 기반. 나프타 공급 위기로 봉투 품귀 → 검색 수요 잡기.

## 현재 상태: Phase 4 완료 (외부 트래픽 활성화 직전)

- 사이트 라이브: https://bag.fazr.co.kr
- 데이터: 전국 69,615곳 (17시도, 229구군시)
- 정적 페이지: 253개 (251 지역 + 2 아티클)
- SEO 최적화 완료
- CTR 최적화 완료
- 아티클 2개 작성 완료
- 네이버 블로그 배포 템플릿 준비 완료

## 기술 스택

- Next.js 14 App Router + ISR (revalidate=86400)
- TailwindCSS v4
- Vercel + 가비아 도메인 (bag.fazr.co.kr)
- 정적 JSON 데이터 (API 호출 없음)
- Python 스크립트 (수집/분류)

## 프로젝트 구조

```
app/
  page.tsx                          # 홈 (17시도 그리드)
  [region]/page.tsx                 # 시도 페이지
  [region]/[district]/page.tsx      # 구군시 페이지 (핵심)
  article/shortage-2026/page.tsx    # 대란 이유 아티클
  article/why-no-bags/page.tsx      # 블로그 톤 아티클
  sitemap.ts, robots.ts
lib/
  regions.ts    # 229개 slug 매핑
  data.ts       # JSON 리더
  seo.ts        # FAQ + JSON-LD
  types.ts
components/
  store/    StoreCard, StoreList
  region/   RegionGrid, DistrictGrid
  seo/      Breadcrumb, FaqSection
  layout/   Header, Footer
data/
  regions.json
  {region}/index.json
  {region}/{district}.json
  _unmatched.json (4건)
scripts/
  collect.py          # API 수집
  reclassify_all.py   # 전체 재분류 (최신)
  classify_all.py     # 구버전
docs/
  BLOG_POST_NAVER.md  # 네이버 블로그 복붙 템플릿
  gpt/                # GPT 세션 보고서 (이 폴더)
```

## 완료된 작업 순서

1. **데이터 수집** - API 1회 호출로 전국 데이터 확보 (905 API calls)
2. **데이터 재분류** - 주소 normalize + 시도 우선 매칭 (오분류 수정)
3. **SEO 기본** - title "총정리|가격|크기", FAQ 5개(JSON-LD), meta description
4. **CTR 최적화** - 품절 배너, 콘텐츠 블록, 내부링크, 신뢰 시그널
5. **아티클** - shortage-2026(SEO진입), why-no-bags(블로그공유)
6. **외부 배포 준비** - 네이버 블로그 템플릿

## 핵심 기술 결정 (중요)

1. 주소 파싱 기반 분류 (API 코드 사용 안 함)
2. 시/도 먼저 확정 → 그 안에서 구 매칭 (동명 구 오분류 방지)
3. 주소 normalize 필수 (대전→대전광역시 등)
4. 세종 특수 처리 (구 없음 → 전부 sejongsi)
5. 0건 구 = soft 404 방지 (안내 페이지 + FAQ)

## 0건 구 (API 데이터 자체 없음)

서울: 강북구, 중랑구, 송파구
울산: 울주군
강원: 고성군
충남: 부여군, 청양군, 당진시

## 남은 작업

1. **Google Search Console** 등록 + sitemap 제출 (수동)
2. **네이버 블로그** 게시 (docs/BLOG_POST_NAVER.md 복붙)
3. **색인 요청**: /seoul/gangnam, /gyeonggi/suwon, /busan/haeundae
4. **AdSense** 광고 연동
5. **트래픽 모니터링** 시작

## 사용자 작업 스타일

- 지시서 기반 작업 (항상 지시서 먼저)
- 결과 중심 ("결과 가져와라")
- 간결한 답변 선호
- 작업 전 항상 확인 질문
- 주관적 판단 금지

## API 정보

- 행정안전부_자원환경_쓰레기종량제봉투판매업
- 일일 한도: 10,000건
- localCode 전국: 6110000_ALL (서울 코드지만 전국 반환)
- 필터: SALS_STTS_CD="01" (영업/정상)
