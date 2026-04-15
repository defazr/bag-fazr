# bag.fazr.co.kr 클로드 세션 보고서

> 새 Claude 세션에서 컨텍스트 파악용
> 최종 업데이트: 2026-04-15

## 현재 상태: 운영 단계 (색인 가속 중)

사이트 라이브: https://bag.fazr.co.kr
데이터: 전국 69,265곳 | 페이지: 252개 | SEO+CTR+디자인+광고+데이터품질+검색UX+내부링크+크롤링가속 완료
색인 상황: 5개 고착 (17일) → P16 구조 강화 + 수동 색인 요청 완료 → 4/18~4/20 체크

## 완료된 Phase

| Phase | 내용 | 상태 |
|---|---|---|
| 1. 데이터 | API 수집 + 주소 기반 재분류 | 완료 |
| 2. SEO | title/desc/FAQ/JSON-LD/sitemap | 완료 |
| 3. CTR | 품절배너/콘텐츠블록/내부링크/신뢰시그널 | 완료 |
| 4. 콘텐츠 | 아티클 2개 + 네이버 블로그 템플릿 | 완료 |
| 5. 광고 | AdSense 4슬롯 활성화 + 레이아웃 안정화 | 완료 |
| 6. 데이터 품질 | collect.py v2 + 세종 복구 + dedupe | 완료 |
| 7. 검색 UX | alias 검색 + 신뢰 문구 + 광고 위치 | 완료 |
| 8. CTR 카드 | District 카드 화살표 + hover | 완료 |
| 9. 내부링크 | Article → 지역 RegionLinks 컴포넌트 | 완료 |
| 10. 크롤링 가속 | 홈 순서 재배치 + article 본문 인라인 링크 | 완료 |

## 프로젝트 구조

```
app/
  page.tsx                          # 홈
  [region]/page.tsx                 # 시도
  [region]/[district]/page.tsx      # 구군시 (핵심)
  article/shortage-2026/page.tsx    # 대란 이유 (SEO 진입)
  article/why-no-bags/page.tsx      # 블로그 톤 (외부 공유)
  layout.tsx                        # AdSense + GA4 <script> in <head>
  globals.css                       # ticker + slide-in animation
  sitemap.ts, not-found.tsx
lib/   regions.ts, data.ts, seo.ts, types.ts
components/
  store/   StoreCard, StoreList (alias 검색)
  region/  RegionGrid, DistrictGrid (화살표 CTR)
  seo/     Breadcrumb, FaqSection
  article/ RegionLinks (6개 지역 chip, SEO 내부링크)
  layout/  Header, Footer, NoticeBanner, MobileMenu, ThemeToggle, ScrollToTop
  ads/     AdSlot, StickyBottomAd
data/  regions.json, {region}/, _unmatched.json
scripts/  collect.py (v2: 1회 수집 + 주소 파싱 + 세종 예외 + dedupe)
docs/  SESSION_REPORT.md, BLOG_POST_NAVER.md, gpt/
```

## 핵심 기술 결정

1. 주소 파싱 기반 분류 (API 코드 사용 안 함)
2. 시/도 먼저 확정 → 그 안에서 구 매칭
3. 주소 normalize 필수 (대전→대전광역시 등)
4. 세종 특수 처리 (구 없음 → sejongsi 직접 매핑)
5. 0건 구 = "판매처 정보 없음" 표시 (soft 404 방지)
6. AdSense: next/script 사용 금지 → 일반 `<script>` 태그
7. 광고 컨테이너: fixed/sticky 금지 → 일반 흐름
8. data-full-width-responsive="false" 필수
9. 검색: alias 매핑 (CU→씨유, GS→GS25 등)
10. 광고 위치: 리스트 아래 (제목 아래 ❌)
11. Article 내부링크: RegionLinks 컴포넌트 (CTA 하단 → RegionLinks → 정리 섹션)
12. 홈 지역 순서: 서울 → 경기 → 부산 → 나머지 (SEO 우선순위)
13. Article 본문 인라인 링크: 서울/경기/부산 (본문 링크 = 가장 강한 크롤링 신호)

## AdSense 설정

| 위치 | Slot ID | 페이지 |
|------|---------|--------|
| 리스트 아래 | 8836749083 | 홈, region |
| 리스트 아래 | 7831623329 | district |
| 하단 | 6518541657 | 홈, region, district |
| 모바일 하단 | 3611374960 | 전체 (StickyBottomAd, sm:hidden) |

## GA4
- ID: G-WTTDTMNTWQ
- 위치: layout.tsx `<head>` 일반 `<script>` 태그

## 0건 구 (API 원본에 데이터 없음)

서울 강북구/중랑구/송파구, 울산 울주군, 강원 고성군, 충남 부여군/청양군/당진시

## 남은 작업

1. GSC 색인 변화 확인 (4/18~4/20 — P16 + 수동 색인 효과 동시 관측)
2. 네이버 블로그 게시 (docs/BLOG_POST_NAVER.md)
3. 트래픽 모니터링 (GA4 + Search Console)
4. 가격 전용 페이지 제작 (추후)
5. 데이터 갱신 구조 검토 (추후)

## 사용자 작업 스타일

- 지시서 기반 작업 (새 세션 = 지시서 대기)
- 결과 중심, 간결한 답변
- 작업 전 항상 확인 질문
- GPT 지시서 오면 반드시 의견 제시 (GPT가 맥락 잃고 잘못된 지시 줄 때 막아야 함)
- 중간 끊긴 작업은 이어하지 말고 처음부터 다시
- 메모리/보고서 저장 시 확인 요청
