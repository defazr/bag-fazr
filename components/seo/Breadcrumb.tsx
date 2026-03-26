import Link from "next/link";

interface BreadcrumbItem {
  label: string;
  href?: string;
}

export default function Breadcrumb({ items }: { items: BreadcrumbItem[] }) {
  return (
    <nav aria-label="breadcrumb" className="mb-4 text-sm text-gray-500 dark:text-gray-400">
      <ol className="flex flex-wrap items-center gap-1">
        <li>
          <Link href="/" className="hover:text-gray-700 dark:hover:text-gray-200">
            홈
          </Link>
        </li>
        {items.map((item, i) => (
          <li key={i} className="flex items-center gap-1">
            <span>/</span>
            {item.href ? (
              <Link href={item.href} className="hover:text-gray-700 dark:hover:text-gray-200">
                {item.label}
              </Link>
            ) : (
              <span className="text-gray-900 dark:text-white">{item.label}</span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}
