import { generateFaqSchema } from "@/lib/seo";

interface FaqSectionProps {
  faqs: { question: string; answer: string }[];
}

export default function FaqSection({ faqs }: FaqSectionProps) {
  const schema = generateFaqSchema(faqs);

  return (
    <section className="mt-10">
      <h2 className="text-xl font-bold text-gray-900 mb-4">자주 묻는 질문</h2>
      <div className="space-y-4">
        {faqs.map((faq, i) => (
          <details
            key={i}
            className="rounded-lg border border-gray-200 bg-white"
          >
            <summary className="cursor-pointer px-4 py-3 font-medium text-gray-900 hover:bg-gray-50">
              {faq.question}
            </summary>
            <p className="px-4 pb-3 text-gray-600">{faq.answer}</p>
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
