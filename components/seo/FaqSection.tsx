import { generateFaqSchema } from "@/lib/seo";

interface FaqSectionProps {
  faqs: { question: string; answer: string }[];
}

export default function FaqSection({ faqs }: FaqSectionProps) {
  const schema = generateFaqSchema(faqs);

  return (
    <section className="mt-12 border-t border-gray-200 dark:border-zinc-800 pt-10">
      <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-4">자주 묻는 질문</h2>
      <div className="space-y-3">
        {faqs.map((faq, i) => (
          <details
            key={i}
            className="rounded-xl border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900"
          >
            <summary className="cursor-pointer px-5 py-3 font-medium text-gray-900 dark:text-white hover:bg-gray-50 dark:hover:bg-zinc-800 rounded-xl transition duration-200">
              {faq.question}
            </summary>
            <p className="px-5 pb-4 text-gray-600 dark:text-zinc-400">{faq.answer}</p>
          </details>
        ))}
      </div>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
      />
    </section>
  );
}
