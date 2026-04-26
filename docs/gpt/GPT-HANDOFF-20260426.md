# GPT 핸드오프 — 2026-04-26 세션

> 이 문서는 GPT에게 오늘 세션 작업 내용을 전달하기 위한 것입니다.
> 이전 전체 컨텍스트: `docs/gpt/SESSION_REPORT.md` 참조
> 이전 핸드오프: `docs/gpt/GPT-HANDOFF-20260415.md` (P16)

---

## 오늘 한 일: P17 + P17.5 + 핫픽스

### P17 — where-to-buy 허브 페이지 + 양방향 내부링크

#### 배경
- Google "쓰레기봉투 파는곳" 키워드 60~61위 고착 (전용 페이지 없음)
- 네이버 "종량제봉투 파는곳" MO 12,800 / "쓰레기봉투 파는곳" MO 6,020
- ���인 5→8 회복 시작 → 확장 타이밍

#### 작업 1: 신규 article 생성

**파일:** `app/article/where-to-buy/page.tsx`

**URL:** `/article/where-to-buy`

**구조:**
```
Breadcrumb
article
  header (h1 + 날짜)
  즉시 클릭 영역 (서울/경기/부산 인라인 링크)
  섹션 1: 도입부 → shortage-2026 인라인 링크
  섹션 2: 지역별 판��처 바로가기 (★ 허브 — 17개 시/도 전부 링크)
  CTA 중간 (키��드 문장 + CTA 블록)
  섹션 3: 파는 곳 종류 (편의점/슈퍼/마트/주민센터/온라인)
  섹션 4: 편의점 종량제봉투 (독립 섹션)
  섹션 5: 가격/사이즈 (키워�� 흡수)
  섹션 6: 구매 팁 → why-no-bags 인라인 링크
  CTA 하단
  RegionLinks (6개 지역 chip)
  섹션 7: 정리
/article
FaqSection (4문항 + JSON-LD)
신뢰 시그널
```

**SEO 키워드 분산 (카니발리제이션 방지):**
| 페이지 | 담당 키워드 |
|--------|------------|
| where-to-buy | 파는곳, 구매, 편의점, 판매처, 가격, 사이즈 |
| shortage-2026 | 대란, 없으면, 품절, 품귀 |
| why-no-bags | 경험, 후기, 상황 |

#### 작업 2: 양방향 내부링크 구축

**shortage-2026 → where-to-buy:**
- 섹션 4 "그냥 찾아다니지 마세요" 내부, P16 인라인 링크 다음 `<p>`
- "판매처를 지역별로 한 번에 확인하고 싶다면 **전국 판매처 총정리**를 참고하세요."

**why-no-bags → where-to-buy:**
- 섹션 4 "무작정 찾아다니면" 내부, P16 인라인 링크 다음 `<p>`
- "전국 판매처를 한눈에 확인하려면 **쓰레기봉투 파는곳 총정리**를 함께 보시면 도움이 됩니다."

**where-to-buy → shortage-2026:**
- 섹션 1 도입부: "�� 봉투가 부족한 건지 궁금하다면 **2026 종량제 봉투 대란 이유**를 함께 보시면 도움이 됩니다."

**where-to-buy → why-no-bags:**
- 섹션 6 구매 팁: "직접 겪어본 후기가 궁금하다면 **종량제 봉투 요즘 왜 없을까**를 함께 읽어보세요."

#### 작업 3: 17개 시/도 역방향 링크

**파일:** `app/[region]/page.tsx`

**위치:** AdSlot(리스트아래)과 FaqSection 사이

**코드:**
```tsx
<div className="mt-6 mb-6">
  <p className="text-sm text-gray-600 dark:text-zinc-400">
    종량제봉투 어디서 ���는지 한눈에 보려면{" "}
    <Link href="/article/where-to-buy" className="font-medium underline underline-offset-2 ...">
      전국 판매처 총정리
    </Link>
    를 확인하세요.
  </p>
  <p className="mt-1 text-xs text-gray-500 dark:text-zinc-500">
    지역별 판매처 기준과 구매 방법을 정리한 페이지입니다.
  </p>
</div>
```

#### 작업 4: sitemap 추가

`app/sitemap.ts`에 `/article/where-to-buy` 수동 추가 (priority 0.7, weekly)

#### 커밋
```
8e47352 P17: where-to-buy 허브 페이지 + 양방향 내부링크 구축
```

---

### P17.5 — 홈 카드 확장 + 햄버거 메뉴

#### 작업 1: 홈 article 카드 2개 → 3개

**파일:** `app/page.tsx`

**변경:**
- 섹션 제목: "종량제 봉투, 요즘 왜 이런가요?" → "종량제 봉투 가이드"
- grid: `sm:grid-cols-2` → `sm:grid-cols-2 lg:grid-cols-3`
- where-to-buy 카드를 **첫 번째**로 배치 (허브 우선순위)
- 카드 제목 키워드 보강: "쓰레기봉투 파는곳 총정리 (종량제봉투 판매처)"

#### 작업 2: 햄버거 메뉴 정보 그룹 2개 → 3개

**파일:** `components/layout/MobileMenu.tsx`

**변경:** ③ 정보 그룹에 where-to-buy 첫 번째로 추가

| 위치 | Before | After |
|------|--------|-------|
| 1번째 | why-no-bags | **where-to-buy** |
| 2번째 | shortage-2026 | why-no-bags |
| 3번째 | (없음) | shortage-2026 |

#### 커밋
```
ae09f66 P17.5: 홈 카드 3개 확장 + 햄버거 메뉴 where-to-buy 추가
```

---

### 핫픽스 — shortage-2026 한글 깨짐 복구

**원인:** P17 Edit 시 한글 바이트 손상
- "내 주변에" → "내 주변\uFFFD" (U+FFFD)
- "움직이는" → "\uFFFD직이는"

**복구:** git diff로 원본 확인 후 정상 한글로 복구

#### 커밋
```
5215934 Fix: shortage-2026 한글 깨짐 복구 (내 주변에/움직이는)
```

---

## SSOT 준수 확인
- blue 사용 없음
- dark:gray 사용 없음 (전부 dark:zinc)
- 기존 구조 미변경 (확장만)
- 빌드 성공 (253페이지)

---

## 현재 프로젝트 상태

- P1~P17.5 완료
- 운영 단계 유지
- 색인: 8개 → P17 허브 + 양방향 링크 + 홈/메뉴 진입 동선 완성
- Article: 3개 (shortage-2026, why-no-bags, where-to-buy)
- 페이지: 253개

## 현재 내부링크 구조 (P17.5 후)

```
홈 (/) ──→ where-to-buy (카드 1번째)
         ──→ shortage-2026 (카드 2번째)
         ──→ why-no-bags (카드 3번째)

햄버거 메뉴 ──→ where-to-buy (정보 1번째)
             ──→ why-no-bags (정보 2번째)
             ──→ shortage-2026 (정보 3번째)

where-to-buy ──→ 17개 시/도 (섹션 2 허브)
             ──→ shortage-2026 (섹션 1 인라인)
             ──→ why-no-bags (섹션 6 인라인)
             ──→ 서울/경기/부산 (즉시 클릭 영역)
             ──→ RegionLinks 6개 지역

shortage-2026 ──→ where-to-buy (섹션 4 인라인)
              ──→ 서울/경기/부산 (P16 인라인)
              ──→ RegionLinks 6개 지역

why-no-bags ──→ where-to-buy (섹션 4 인라인)
            ──→ 서울/경기/부산 (P16 인라인)
            ──→ RegionLinks 6개 지역

17개 시/도 ──→ where-to-buy (AdSlot↔FaqSection 사이)
```

## 다음 단계

1. **GSC 수동 색인 요청 5건** (배포 확인 후 즉시)
   - `/` (홈), `/article/where-to-buy`, `/seoul`, `/gyeonggi`, `/busan`
2. **4/29 체크포인트** — 색인 8→10+ 목표
3. **P18 방향 결정** (4/29 결과 기반)
   - A: price 페이지 (MO 22,200)
   - B: 편의점별 페이지 (CU/GS25/세븐)
   - C: 네이버 블로그 게시

---

## 기대 효과

- where-to-buy = SEO 허브로 모든 지역 페이지에 PageRank 전달
- 홈 ��� 허브 → 지역 크롤링 경로 완성
- "쓰레기봉투 파는곳" 전용 페이지 확보 → 60위 → 상위 진입 목표
- 3개 article 간 양��향 링크로 topical authority 강화
