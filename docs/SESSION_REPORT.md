# bag.fazr.co.kr 클로드 세션 보고서

> 새 Claude 세션에서 컨텍스트 파악용
> 최종 업데이트: 2026-04-26

## 현재 상태: 운영 단계 (P17 허브 구축 완료, 색인 확장 대기)

사이트 라이브: https://bag.fazr.co.kr
데이터: 전국 69,265곳 | 페이지: 253개 | Article: 3개
색인 상황: 8개 → P17 허브 + 양방향 링크 완성 → GSC 색인 요청 5건 예정 → 4/29 체크

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
| 11. 허브 article | where-to-buy + 양방향 내부링크 + 홈/메뉴 동선 | 완료 |

## 프로젝트 구조

```
app/
  page.tsx                          # 홈 (카드 3개: where-to-buy, shortage, why-no-bags)
  [region]/page.tsx                 # 시도 (+ where-to-buy 역��향 링크)
  [region]/[district]/page.tsx      # 구군시 (핵심)
  article/where-to-buy/page.tsx     # 쓰레기봉투 파는곳 총정리 (SEO 허브)
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
  layout/  Header, Footer, NoticeBanner, MobileMenu (3단+where-to-buy), ThemeToggle, ScrollToTop
  ads/     AdSlot, StickyBottomAd
data/  regions.json, {region}/, _unmatched.json
scripts/  collect.py (v2: 1회 수집 + 주소 파싱 + 세종 예외 + dedupe)
docs/  SESSION_REPORT.md, BLOG_POST_NAVER.md, gpt/
```

## 내부링크 구조 (P17.5 후)

```
홈 → where-to-buy(카드1), shortage(카드2), why-no-bags(카드3)
햄버거 → where-to-buy(정보1), why-no-bags(정보2), shortage(정보3)
where-to-buy → 17개 시/도(허브), shortage(인라인), why-no-bags(인라인)
shortage → where-to-buy(인라인), 서울/경기/부산(P16)
why-no-bags → where-to-buy(인라인), 서울/경기/부산(P16)
17개 시/도 → where-to-buy(역방향링크)
```

## 핵심 기술 결정

1. 주소 파싱 기반 분류 (API 코드 사용 안 함)
2. 세종 특수 처리 (구 없음 → sejongsi 직접 매핑)
3. AdSense: next/script 사용 금지 → 일반 `<script>` 태그
4. 광고 컨테이너: fixed/sticky 금지 → 일반 흐름
5. data-full-width-responsive="false" 필수
6. 검색: alias 매핑 (CU→씨유, GS→GS25 등)
7. Article 인라인 링크: font-medium underline underline-offset-2 (blue 금지)
8. where-to-buy = 허브 (17개 시/도 링크 + 3개 article 양방향)
9. 홈 article 카드: lg:grid-cols-3, where-to-buy 첫 번째

## AdSense 설정

| 위치 | Slot ID | 페이지 |
|------|---------|--------|
| 리스트 아래 | 8836749083 | 홈, region |
| 리스트 아래 | 7831623329 | district |
| 하단 | 6518541657 | 홈, region, district |
| 모바일 하단 | 3611374960 | 전체 (StickyBottomAd, sm:hidden) |

## 남은 작업

1. GSC 수동 색인 요청 5건 (/, /article/where-to-buy, /seoul, /gyeonggi, /busan)
2. 4/29 체크포인트: 색인 8→10+ 확인
3. P18 방향 결정 (price 페이지 유력)
4. 네이버 블로그 게시 (docs/BLOG_POST_NAVER.md)
5. 데이터 갱신 구조 검토 (추후)

## 사용자 작업 스타일

- 지시서 기반 작업 (새 세션 = 지시서 대기)
- 결과 중심, 간결한 답변
- 작업 전 항상 확인 질문
- GPT 지시서 오면 반드시 의견 제시 (GPT가 맥락 잃고 잘못된 지시 줄 때 막아야 함)
- 중간 끊긴 작업은 이어하지 말고 처음부터 다시
- 메모리/보고서 저장 시 확인 요청
- docs/md 파���만 커밋 시 [skip ci] 붙이기
