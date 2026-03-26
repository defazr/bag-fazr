import type { MetadataRoute } from "next";
import { REGIONS, getDistrictsByRegion } from "@/lib/regions";
import { getRegionIndex } from "@/lib/data";

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = "https://bag.fazr.co.kr";
  const entries: MetadataRoute.Sitemap = [
    { url: baseUrl, lastModified: new Date(), changeFrequency: "daily", priority: 1 },
  ];

  for (const region of REGIONS) {
    entries.push({
      url: `${baseUrl}/${region.slug}`,
      lastModified: new Date(),
      changeFrequency: "daily",
      priority: 0.8,
    });

    const regionIndex = getRegionIndex(region.slug);
    if (regionIndex) {
      for (const d of regionIndex.districts) {
        if (d.count > 0) {
          entries.push({
            url: `${baseUrl}/${region.slug}/${d.districtSlug}`,
            lastModified: new Date(),
            changeFrequency: "daily",
            priority: 0.9,
          });
        }
      }
    }
  }

  return entries;
}
