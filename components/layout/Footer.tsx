export default function Footer() {
  return (
    <footer className="border-t border-gray-200 bg-gray-50 mt-12 dark:border-gray-800 dark:bg-gray-900">
      <div className="mx-auto max-w-4xl px-4 py-8 text-sm text-gray-500 dark:text-gray-400">
        <p>
          본 서비스는 공공데이터포털의 데이터를 활용하며, 실제 영업 여부 및
          재고 상황은 해당 판매처에 직접 확인하시기 바랍니다.
        </p>
        <p className="mt-2">
          데이터 출처: 행정안전부 자원환경 쓰레기종량제봉투판매업 조회서비스
        </p>
        <p className="mt-1">© 2026 bag.fazr.co.kr</p>
      </div>
    </footer>
  );
}
