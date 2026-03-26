# bag.fazr.co.kr 클로드 세션 보고서

> 새 Claude 세션에서 컨텍스트 파악용

## 현재 상태: Phase 5 완료 (광고 활성화 + 트래픽 확산 중)

사이트 라이브: https://bag.fazr.co.kr
데이터: 전국 69,615곳 | 페이지: 253개 | SEO+CTR+디자인+광고 완료

## 완료된 Phase

| Phase | 내용 | 상태 |
|---|---|---|
| 1. 데이터 | API 수집 + 주소 기반 재분류 | 완료 |
| 2. SEO | title/desc/FAQ/JSON-LD/sitemap | 완료 |
| 3. CTR | 품절배너/콘텐츠블록/내부링크/신뢰시그널 | 완료 |
| 4. 콘텐츠 | 아티클 2개 + 네이버 블로그 템플릿 | 완료 |
| 5. 광고 | AdSense 4슬롯 활성화 + 레이아웃 안정화 | 완료 |

## 프로젝트 구조

```
app/
  page.tsx                          # 홈
  [region]/page.tsx                 # 시도
  [region]/[district]/page.tsx      # 구군시 (핵심)
  article/shortage-2026/page.tsx    # 대란 이유 (SEO 진입)
  article/why-no-bags/page.tsx      # 블로그 톤 (외부 공유)
  layout.tsx                        # AdSense <script> in <head>
  globals.css                       # ticker + slide-in animation
  sitemap.ts, not-found.tsx
lib/   regions.ts, data.ts, seo.ts, types.ts
components/
  store/   StoreCard, StoreList
  region/  RegionGrid, DistrictGrid
  seo/     Breadcrumb, FaqSection
  layout/  Header, Footer, NoticeBanner, MobileMenu, ThemeToggle, ScrollToTop
  ads/     AdSlot, StickyBottomAd
data/  regions.json, {region}/, _unmatched.json
scripts/  collect.py, reclassify_all.py
docs/  SESSION_REPORT.md, BLOG_POST_NAVER.md, gpt/
```

## 핵심 기술 결정

1. 주소 파싱 기반 분류 (API 코드 사용 안 함)
2. 시/도 먼저 확정 → 그 안에서 구 매칭
3. 주소 normalize 필수 (대전→대전광역시 등)
4. 세종 특수 처리 (구 없음 → sejongsi)
5. 0건 구 = soft 404 방지 (안내+FAQ+인접링크)
6. AdSense: next/script 사용 금지 → 일반 `<script>` 태그 (data-nscript 에러)
7. 광고 컨테이너: fixed/sticky 금지 → 일반 흐름
8. data-full-width-responsive="false" 필수

## AdSense 설정 (활성화 완료)

| 위치 | Slot ID | 페이지 |
|------|---------|--------|
| 상단 | 8836749083 | 홈, region |
| 리스트 아래 | 7831623329 | district |
| 하단 | 6518541657 | 홈, region, district |
| 모바일 하단 | 3611374960 | 전체 (StickyBottomAd, sm:hidden) |

### AdSense 주의사항
- `next/script` 사용 금지 → `<head>`에 일반 `<script>` 태그
- `data-full-width-responsive="false"` 필수 (컨테이너 밖 확장 방지)
- 광고 컨테이너: 플랫 (border/padding 없음, 일반 div만)
- StickyBottomAd: max-h-[100px] + format="fluid" + sm:hidden
- AdSlot: mount guard + pushed ref 이중 가드로 중복 방지

## 0건 구

서울 강북구/중랑구/송파구, 울산 울주군, 강원 고성군, 충남 부여군/청양군/당진시

## 남은 작업

1. 네이버 블로그 게시 (docs/BLOG_POST_NAVER.md)
2. 트래픽 모니터링
3. 가격 전용 페이지 제작 (추후)
4. 데이터 갱신 구조 검토 (추후)

## 사용자 작업 스타일

- 지시서 기반 작업 (새 세션 = 지시서 대기)
- 결과 중심, 간결한 답변
- 작업 전 항상 확인 질문
- GPT 지시서 오면 반드시 의견 제시 (GPT가 맥락 잃고 잘못된 지시 줄 때 막아야 함)
- 중간 끊긴 작업은 이어하지 말고 처음부터 다시
- 메모리/보고서 저장 시 확인 요청
