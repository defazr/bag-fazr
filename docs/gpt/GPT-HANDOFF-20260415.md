# GPT 핸드오프 — 2026-04-15 세션

> 이 문서는 GPT에게 오늘 세션 작업 내용을 전달하기 위한 것입니다.
> 이전 전체 컨텍스트: `docs/SESSION_REPORT.md` 참조
> 이전 핸드오프: `docs/gpt/GPT-HANDOFF-20260405.md` (P15)

---

## 오늘 한 일: P16 — 크롤링 가속 (홈 재배치 + 본문 인라인 링크)

### 배경
- P15 배포(4/5) 후 10일 경과, 색인 5개 그대로 (17일 연속 고착)
- GSC 수동 색인 요청 + sitemap 재제출은 사용자가 별도 진행
- P16은 **구조적 크롤링 신호 강화** — "배치가 SEO다"

### 작업 내용

#### 작업 1: 홈 시/도 순서 재배치

**수정 파일:** `data/regions.json`

**변경:**
- 기존: slug 알파벳순 (busan → chungbuk → ... → seoul → ulsan)
- 변경: **서울(1) → 경기(2) → 부산(3)** → 나머지 14개 기존 순서 유지

**핵심:**
- `data/regions.json` 순서 = `getRegionsData()` → `RegionGrid` 렌더링 순서
- 디자인/구조/스타일 변경 없음. 순서만 변경.
- Google 크롤러에 주요 지역 중요도 재선언

#### 작업 2: article 본문 인라인 링크 추가

**수정 파일:**
- `app/article/shortage-2026/page.tsx`
- `app/article/why-no-bags/page.tsx`

**shortage-2026 — "그냥 찾아다니지 마세요" 섹션:**
```
기존: "...지역별로 정리해둔 데이터가 있습니다. 내 주변에..."
변경: "...지역별로 정리해둔 데이터가 있습니다. 서울 / 경기 / 부산 등 주요 지역은 바로 확인할 수 있습니다. 내 주변에..."
```

**why-no-bags — "무작정 찾아다니면" 섹션:**
```
기존: "...정리해둔 데이터가 있었습니다. 미리 확인했으면..."
변경: "...정리해둔 데이터가 있었습니다. 서울, 경기, 부산 등 주요 지역은 바로 확인 가능합니다. 미리 확인했으면..."
```

**링크 스타일 (SSOT v1.7 준수):**
```tsx
className="font-medium underline underline-offset-2 hover:text-gray-900 dark:hover:text-white transition"
```
- 본문 텍스트 색상 상속 (별도 색 지정 ❌)
- blue 금지 ✔

### 커밋
```
615e669 P16: Crawl priority boost - reorder regions + inline article links
```

### SSOT 준수 확인
- blue 사용 없음 ✔
- 기존 구조(CTA, RegionLinks, FAQ, 신뢰시그널, Breadcrumb) 미변경 ✔
- 빌드 성공 (252페이지 전부 생성) ✔
- Vercel 자동 배포 완료 ✔

---

## 현재 프로젝트 상태

- P1~P16 완료
- 운영 단계 유지
- 색인: 5개 고착 → P16 + 수동 색인 요청으로 구조적 신호 강화 완료

## Article 페이지 현재 구조 (P16 후)

```
Breadcrumb
article
  header (h1 + 날짜)
  본문 섹션 1~3
  본문 섹션 4 ← 서울/경기/부산 인라인 링크 삽입 (P16 신규)
  CTA 중간 (href="/")
  본문 섹션 5~6
  CTA 하단 (href="/")
  RegionLinks (서울/경기/부산/인천/대구/광주)  ← P15
  정리 섹션
/article
FaqSection
신뢰 시그널
```

## 홈 "지역별 판매처" 순서 (P16 후)

```
1. 서울특별시     ← P16 이동
2. 경기도         ← P16 이동
3. 부산광역시     (기존 1번 → 3번)
4~17. 나머지 기존 순서 유지
```

## 다음 단계

1. **GSC 색인 변화 확인 (4/18~4/20)** — P16 + 수동 색인 효과 동시 관측
2. 네이버 블로그 게시 (docs/BLOG_POST_NAVER.md)
3. 트래픽 모니터링 (GA4 + Search Console)
4. 가격 전용 페이지 제작 (추후)
5. 데이터 갱신 구조 검토 (추후)

---

## 기대 효과

- 홈 RegionGrid에서 서울/경기/부산이 최상단 → 크롤러 우선 발견
- article 본문 인라인 링크 = 가장 강한 SEO 신호 (본문 링크 > 사이드바/푸터 링크)
- 수동 색인 요청(별도 진행)과 합산 시 3~5일 내 색인 변화 기대
