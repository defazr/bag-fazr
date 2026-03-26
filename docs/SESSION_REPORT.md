# bag.fazr.co.kr 클로드 세션 보고서

> 새 Claude 세션에서 컨텍스트 파악용

## 현재 상태: Phase 4 완료 (외부 트래픽 활성화 직전)

사이트 라이브: https://bag.fazr.co.kr
데이터: 전국 69,615곳 | 페이지: 253개 | SEO+CTR 최적화 완료

## 완료된 Phase

| Phase | 내용 | 상태 |
|---|---|---|
| 1. 데이터 | API 수집 + 주소 기반 재분류 | 완료 |
| 2. SEO | title/desc/FAQ/JSON-LD/sitemap | 완료 |
| 3. CTR | 품절배너/콘텐츠블록/내부링크/신뢰시그널 | 완료 |
| 4. 콘텐츠 | 아티클 2개 + 네이버 블로그 템플릿 | 완료 |

## 프로젝트 구조

```
app/
  page.tsx                          # 홈
  [region]/page.tsx                 # 시도
  [region]/[district]/page.tsx      # 구군시 (핵심)
  article/shortage-2026/page.tsx    # 대란 이유 (SEO 진입)
  article/why-no-bags/page.tsx      # 블로그 톤 (외부 공유)
  sitemap.ts, robots.ts
lib/   regions.ts, data.ts, seo.ts, types.ts
components/  store/, region/, seo/, layout/
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

## 0건 구

서울 강북구/중랑구/송파구, 울산 울주군, 강원 고성군, 충남 부여군/청양군/당진시

## 남은 작업

1. Google Search Console 등록 + sitemap 제출 (수동)
2. 네이버 블로그 게시 (docs/BLOG_POST_NAVER.md)
3. 색인 요청: /seoul/gangnam, /gyeonggi/suwon, /busan/haeundae
4. AdSense 광고 연동
5. 트래픽 모니터링

## 사용자 작업 스타일

- 지시서 기반 작업 (새 세션 = 지시서 대기)
- 결과 중심, 간결한 답변
- 작업 전 항상 확인 질문
- 주관적 판단 금지
- 메모리/보고서 저장 시 확인 요청
