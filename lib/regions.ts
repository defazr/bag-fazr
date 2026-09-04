import type { RegionMapping, DistrictMapping } from "./types";

export const REGIONS: RegionMapping[] = [
  { name: "서울특별시", slug: "seoul", apiCode: "6110000_ALL" },
  { name: "부산광역시", slug: "busan", apiCode: "6260000_ALL" },
  { name: "대구광역시", slug: "daegu", apiCode: "6270000_ALL" },
  { name: "인천광역시", slug: "incheon", apiCode: "6280000_ALL" },
  { name: "광주광역시", slug: "gwangju", apiCode: "6290000_ALL" },
  { name: "대전광역시", slug: "daejeon", apiCode: "6300000_ALL" },
  { name: "울산광역시", slug: "ulsan", apiCode: "6310000_ALL" },
  { name: "세종특별자치시", slug: "sejong", apiCode: "5690000_ALL" },
  { name: "경기도", slug: "gyeonggi", apiCode: "6410000_ALL" },
  { name: "강원특별자치도", slug: "gangwon", apiCode: "6530000_ALL" },
  { name: "충청북도", slug: "chungbuk", apiCode: "6430000_ALL" },
  { name: "충청남도", slug: "chungnam", apiCode: "6440000_ALL" },
  { name: "전북특별자치도", slug: "jeonbuk", apiCode: "6540000_ALL" },
  { name: "전라남도", slug: "jeonnam", apiCode: "6460000_ALL" },
  { name: "경상북도", slug: "gyeongbuk", apiCode: "6470000_ALL" },
  { name: "경상남도", slug: "gyeongnam", apiCode: "6480000_ALL" },
  { name: "제주특별자치도", slug: "jeju", apiCode: "6500000_ALL" },
];

export const DISTRICTS: DistrictMapping[] = [
  // ===== 서울특별시 (25개구) =====
  { name: "강남구", slug: "gangnam", regionSlug: "seoul", apiCode: "3220000" },
  { name: "강동구", slug: "gangdong", regionSlug: "seoul", apiCode: "3240000" },
  { name: "강북구", slug: "gangbuk", regionSlug: "seoul", apiCode: "3080000" },
  { name: "강서구", slug: "gangseo", regionSlug: "seoul", apiCode: "3150000" },
  { name: "관악구", slug: "gwanak", regionSlug: "seoul", apiCode: "3200000" },
  { name: "광진구", slug: "gwangjin", regionSlug: "seoul", apiCode: "3040000" },
  { name: "구로구", slug: "guro", regionSlug: "seoul", apiCode: "3160000" },
  { name: "금천구", slug: "geumcheon", regionSlug: "seoul", apiCode: "3170000" },
  { name: "노원구", slug: "nowon", regionSlug: "seoul", apiCode: "3100000" },
  { name: "도봉구", slug: "dobong", regionSlug: "seoul", apiCode: "3090000" },
  { name: "동대문구", slug: "dongdaemun", regionSlug: "seoul", apiCode: "3050000" },
  { name: "동작구", slug: "dongjak", regionSlug: "seoul", apiCode: "3190000" },
  { name: "마포구", slug: "mapo", regionSlug: "seoul", apiCode: "3130000" },
  { name: "서대문구", slug: "seodaemun", regionSlug: "seoul", apiCode: "3120000" },
  { name: "서초구", slug: "seocho", regionSlug: "seoul", apiCode: "3210000" },
  { name: "성동구", slug: "seongdong", regionSlug: "seoul", apiCode: "3030000" },
  { name: "성북구", slug: "seongbuk", regionSlug: "seoul", apiCode: "3070000" },
  { name: "송파구", slug: "songpa", regionSlug: "seoul", apiCode: "3230000" },
  { name: "양천구", slug: "yangcheon", regionSlug: "seoul", apiCode: "3140000" },
  { name: "영등포구", slug: "yeongdeungpo", regionSlug: "seoul", apiCode: "3180000" },
  { name: "용산구", slug: "yongsan", regionSlug: "seoul", apiCode: "3020000" },
  { name: "은평구", slug: "eunpyeong", regionSlug: "seoul", apiCode: "3110000" },
  { name: "종로구", slug: "jongno", regionSlug: "seoul", apiCode: "3000000" },
  { name: "중구", slug: "junggu", regionSlug: "seoul", apiCode: "3010000" },
  { name: "중랑구", slug: "jungnang", regionSlug: "seoul", apiCode: "3060000" },

  // ===== 부산광역시 (16개 구/군) =====
  { name: "강서구", slug: "bsgangseo", regionSlug: "busan", apiCode: "3360000" },
  { name: "금정구", slug: "geumjeong", regionSlug: "busan", apiCode: "3350000" },
  { name: "기장군", slug: "gijang", regionSlug: "busan", apiCode: "3400000" },
  { name: "남구", slug: "bsnamgu", regionSlug: "busan", apiCode: "3310000" },
  { name: "동구", slug: "bsdonggu", regionSlug: "busan", apiCode: "3270000" },
  { name: "동래구", slug: "dongnae", regionSlug: "busan", apiCode: "3300000" },
  { name: "부산진구", slug: "busanjin", regionSlug: "busan", apiCode: "3290000" },
  { name: "북구", slug: "bsbukgu", regionSlug: "busan", apiCode: "3320000" },
  { name: "사상구", slug: "sasang", regionSlug: "busan", apiCode: "3390000" },
  { name: "사하구", slug: "saha", regionSlug: "busan", apiCode: "3340000" },
  { name: "서구", slug: "bsseogu", regionSlug: "busan", apiCode: "3260000" },
  { name: "수영구", slug: "suyeong", regionSlug: "busan", apiCode: "3380000" },
  { name: "연제구", slug: "yeonje", regionSlug: "busan", apiCode: "3370000" },
  { name: "영도구", slug: "yeongdo", regionSlug: "busan", apiCode: "3280000" },
  { name: "중구", slug: "bsjunggu", regionSlug: "busan", apiCode: "3250000" },
  { name: "해운대구", slug: "haeundae", regionSlug: "busan", apiCode: "3330000" },

  // ===== 대구광역시 (8개 구/군) =====
  { name: "남구", slug: "dgnamgu", regionSlug: "daegu", apiCode: "3440000" },
  { name: "달서구", slug: "dalseo", regionSlug: "daegu", apiCode: "3470000" },
  { name: "달성군", slug: "dalseong", regionSlug: "daegu", apiCode: "3480000" },
  { name: "동구", slug: "dgdonggu", regionSlug: "daegu", apiCode: "3420000" },
  { name: "북구", slug: "dgbukgu", regionSlug: "daegu", apiCode: "3450000" },
  { name: "서구", slug: "dgseogu", regionSlug: "daegu", apiCode: "3430000" },
  { name: "수성구", slug: "suseong", regionSlug: "daegu", apiCode: "3460000" },
  { name: "중구", slug: "dgjunggu", regionSlug: "daegu", apiCode: "3410000" },
  { name: "군위군", slug: "gunwi", regionSlug: "daegu", apiCode: "3490000" },

  // ===== 인천광역시 (10개 구/군) =====
  { name: "계양구", slug: "gyeyang", regionSlug: "incheon", apiCode: "3560000" },
  { name: "남동구", slug: "namdong", regionSlug: "incheon", apiCode: "3550000" },
  { name: "동구", slug: "icdonggu", regionSlug: "incheon", apiCode: "3510000" },
  { name: "미추홀구", slug: "michuhol", regionSlug: "incheon", apiCode: "3520000" },
  { name: "부평구", slug: "bupyeong", regionSlug: "incheon", apiCode: "3540000" },
  { name: "서구", slug: "icseogu", regionSlug: "incheon", apiCode: "3570000" },
  { name: "연수구", slug: "yeonsu", regionSlug: "incheon", apiCode: "3530000" },
  { name: "중구", slug: "icjunggu", regionSlug: "incheon", apiCode: "3500000" },
  { name: "강화군", slug: "ganghwa", regionSlug: "incheon", apiCode: "3580000" },
  { name: "옹진군", slug: "ongjin", regionSlug: "incheon", apiCode: "3590000" },

  // ===== 광주광역시 (5개구) =====
  { name: "광산구", slug: "gwangsan", regionSlug: "gwangju", apiCode: "3640000" },
  { name: "남구", slug: "gjnamgu", regionSlug: "gwangju", apiCode: "3620000" },
  { name: "동구", slug: "gjdonggu", regionSlug: "gwangju", apiCode: "3600000" },
  { name: "북구", slug: "gjbukgu", regionSlug: "gwangju", apiCode: "3630000" },
  { name: "서구", slug: "gjseogu", regionSlug: "gwangju", apiCode: "3610000" },

  // ===== 대전광역시 (5개구) =====
  { name: "대덕구", slug: "daedeok", regionSlug: "daejeon", apiCode: "3690000" },
  { name: "동구", slug: "djdonggu", regionSlug: "daejeon", apiCode: "3650000" },
  { name: "서구", slug: "djseogu", regionSlug: "daejeon", apiCode: "3670000" },
  { name: "유성구", slug: "yuseong", regionSlug: "daejeon", apiCode: "3680000" },
  { name: "중구", slug: "djjunggu", regionSlug: "daejeon", apiCode: "3660000" },

  // ===== 울산광역시 (5개 구/군) =====
  { name: "남구", slug: "usnamgu", regionSlug: "ulsan", apiCode: "3710000" },
  { name: "동구", slug: "usdonggu", regionSlug: "ulsan", apiCode: "3700000" },
  { name: "북구", slug: "usbukgu", regionSlug: "ulsan", apiCode: "3720000" },
  { name: "울주군", slug: "ulju", regionSlug: "ulsan", apiCode: "3730000" },
  { name: "중구", slug: "usjunggu", regionSlug: "ulsan", apiCode: "3740000" },

  // ===== 세종특별자치시 (1개) =====
  { name: "세종시", slug: "sejongsi", regionSlug: "sejong", apiCode: "5690000" },

  // ===== 경기도 (31개 시/군) =====
  { name: "가평군", slug: "gapyeong", regionSlug: "gyeonggi", apiCode: "3870000" },
  { name: "고양시", slug: "goyang", regionSlug: "gyeonggi", apiCode: "3790000" },
  { name: "과천시", slug: "gwacheon", regionSlug: "gyeonggi", apiCode: "3820000" },
  { name: "광명시", slug: "gwangmyeong", regionSlug: "gyeonggi", apiCode: "3780000" },
  { name: "광주시", slug: "ggwangju", regionSlug: "gyeonggi", apiCode: "3850000" },
  { name: "구리시", slug: "guri", regionSlug: "gyeonggi", apiCode: "3830000" },
  { name: "군포시", slug: "gunpo", regionSlug: "gyeonggi", apiCode: "3810000" },
  { name: "김포시", slug: "gimpo", regionSlug: "gyeonggi", apiCode: "3890000" },
  { name: "남양주시", slug: "namyangju", regionSlug: "gyeonggi", apiCode: "3830000" },
  { name: "동두천시", slug: "dongducheon", regionSlug: "gyeonggi", apiCode: "3770000" },
  { name: "부천시", slug: "bucheon", regionSlug: "gyeonggi", apiCode: "3780000" },
  { name: "성남시", slug: "seongnam", regionSlug: "gyeonggi", apiCode: "3760000" },
  { name: "수원시", slug: "suwon", regionSlug: "gyeonggi", apiCode: "3750000" },
  { name: "시흥시", slug: "siheung", regionSlug: "gyeonggi", apiCode: "3800000" },
  { name: "안산시", slug: "ansan", regionSlug: "gyeonggi", apiCode: "3800000" },
  { name: "안성시", slug: "anseong", regionSlug: "gyeonggi", apiCode: "3860000" },
  { name: "안양시", slug: "anyang", regionSlug: "gyeonggi", apiCode: "3760000" },
  { name: "양주시", slug: "yangju", regionSlug: "gyeonggi", apiCode: "3880000" },
  { name: "양평군", slug: "yangpyeong", regionSlug: "gyeonggi", apiCode: "3870000" },
  { name: "여주시", slug: "yeoju", regionSlug: "gyeonggi", apiCode: "3860000" },
  { name: "연천군", slug: "yeoncheon", regionSlug: "gyeonggi", apiCode: "3880000" },
  { name: "오산시", slug: "osan", regionSlug: "gyeonggi", apiCode: "3810000" },
  { name: "용인시", slug: "yongin", regionSlug: "gyeonggi", apiCode: "3840000" },
  { name: "의왕시", slug: "uiwang", regionSlug: "gyeonggi", apiCode: "3820000" },
  { name: "의정부시", slug: "uijeongbu", regionSlug: "gyeonggi", apiCode: "3770000" },
  { name: "이천시", slug: "icheon", regionSlug: "gyeonggi", apiCode: "3850000" },
  { name: "파주시", slug: "paju", regionSlug: "gyeonggi", apiCode: "3890000" },
  { name: "평택시", slug: "pyeongtaek", regionSlug: "gyeonggi", apiCode: "3760000" },
  { name: "포천시", slug: "pocheon", regionSlug: "gyeonggi", apiCode: "3880000" },
  { name: "하남시", slug: "hanam", regionSlug: "gyeonggi", apiCode: "3840000" },
  { name: "화성시", slug: "hwaseong", regionSlug: "gyeonggi", apiCode: "3810000" },

  // ===== 강원특별자치도 (18개 시/군) =====
  { name: "강릉시", slug: "gangneung", regionSlug: "gangwon", apiCode: "3930000" },
  { name: "고성군", slug: "gwgoseong", regionSlug: "gangwon", apiCode: "3960000" },
  { name: "동해시", slug: "donghae", regionSlug: "gangwon", apiCode: "3940000" },
  { name: "삼척시", slug: "samcheok", regionSlug: "gangwon", apiCode: "3950000" },
  { name: "속초시", slug: "sokcho", regionSlug: "gangwon", apiCode: "3950000" },
  { name: "양구군", slug: "yanggu", regionSlug: "gangwon", apiCode: "3960000" },
  { name: "양양군", slug: "yangyang", regionSlug: "gangwon", apiCode: "3970000" },
  { name: "영월군", slug: "yeongwol", regionSlug: "gangwon", apiCode: "3940000" },
  { name: "원주시", slug: "wonju", regionSlug: "gangwon", apiCode: "3920000" },
  { name: "인제군", slug: "inje", regionSlug: "gangwon", apiCode: "3960000" },
  { name: "정선군", slug: "jeongseon", regionSlug: "gangwon", apiCode: "3950000" },
  { name: "철원군", slug: "cheorwon", regionSlug: "gangwon", apiCode: "3960000" },
  { name: "춘천시", slug: "chuncheon", regionSlug: "gangwon", apiCode: "3910000" },
  { name: "태백시", slug: "taebaek", regionSlug: "gangwon", apiCode: "3940000" },
  { name: "평창군", slug: "pyeongchang", regionSlug: "gangwon", apiCode: "3950000" },
  { name: "홍천군", slug: "hongcheon", regionSlug: "gangwon", apiCode: "3930000" },
  { name: "화천군", slug: "hwacheon", regionSlug: "gangwon", apiCode: "3960000" },
  { name: "횡성군", slug: "hoengseong", regionSlug: "gangwon", apiCode: "3920000" },

  // ===== 충청북도 (11개 시/군) =====
  { name: "괴산군", slug: "goesan", regionSlug: "chungbuk", apiCode: "4020000" },
  { name: "단양군", slug: "danyang", regionSlug: "chungbuk", apiCode: "4030000" },
  { name: "보은군", slug: "boeun", regionSlug: "chungbuk", apiCode: "4010000" },
  { name: "영동군", slug: "yeongdong", regionSlug: "chungbuk", apiCode: "4010000" },
  { name: "옥천군", slug: "okcheon", regionSlug: "chungbuk", apiCode: "4010000" },
  { name: "음성군", slug: "eumseong", regionSlug: "chungbuk", apiCode: "4020000" },
  { name: "제천시", slug: "jecheon", regionSlug: "chungbuk", apiCode: "4000000" },
  { name: "증평군", slug: "jeungpyeong", regionSlug: "chungbuk", apiCode: "4020000" },
  { name: "진천군", slug: "jincheon", regionSlug: "chungbuk", apiCode: "4020000" },
  { name: "청주시", slug: "cheongju", regionSlug: "chungbuk", apiCode: "3990000" },
  { name: "충주시", slug: "chungju", regionSlug: "chungbuk", apiCode: "3990000" },

  // ===== 충청남도 (15개 시/군) =====
  { name: "계룡시", slug: "gyeryong", regionSlug: "chungnam", apiCode: "4100000" },
  { name: "공주시", slug: "gongju", regionSlug: "chungnam", apiCode: "4040000" },
  { name: "금산군", slug: "geumsan", regionSlug: "chungnam", apiCode: "4080000" },
  { name: "논산시", slug: "nonsan", regionSlug: "chungnam", apiCode: "4090000" },
  { name: "당진시", slug: "dangjin", regionSlug: "chungnam", apiCode: "4110000" },
  { name: "보령시", slug: "boryeong", regionSlug: "chungnam", apiCode: "4050000" },
  { name: "부여군", slug: "buyeo", regionSlug: "chungnam", apiCode: "4080000" },
  { name: "서산시", slug: "seosan", regionSlug: "chungnam", apiCode: "4060000" },
  { name: "서천군", slug: "seocheon", regionSlug: "chungnam", apiCode: "4090000" },
  { name: "아산시", slug: "asan", regionSlug: "chungnam", apiCode: "4050000" },
  { name: "예산군", slug: "yesan", regionSlug: "chungnam", apiCode: "4090000" },
  { name: "천안시", slug: "cheonan", regionSlug: "chungnam", apiCode: "4040000" },
  { name: "청양군", slug: "cheongyang", regionSlug: "chungnam", apiCode: "4080000" },
  { name: "태안군", slug: "taean", regionSlug: "chungnam", apiCode: "4070000" },
  { name: "홍성군", slug: "hongseong", regionSlug: "chungnam", apiCode: "4070000" },

  // ===== 전북특별자치도 (14개 시/군) =====
  { name: "고창군", slug: "gochang", regionSlug: "jeonbuk", apiCode: "4190000" },
  { name: "군산시", slug: "gunsan", regionSlug: "jeonbuk", apiCode: "4130000" },
  { name: "김제시", slug: "gimje", regionSlug: "jeonbuk", apiCode: "4170000" },
  { name: "남원시", slug: "namwon", regionSlug: "jeonbuk", apiCode: "4150000" },
  { name: "무주군", slug: "muju", regionSlug: "jeonbuk", apiCode: "4180000" },
  { name: "부안군", slug: "buan", regionSlug: "jeonbuk", apiCode: "4200000" },
  { name: "순창군", slug: "sunchang", regionSlug: "jeonbuk", apiCode: "4190000" },
  { name: "완주군", slug: "wanju", regionSlug: "jeonbuk", apiCode: "4170000" },
  { name: "익산시", slug: "iksan", regionSlug: "jeonbuk", apiCode: "4140000" },
  { name: "임실군", slug: "imsil", regionSlug: "jeonbuk", apiCode: "4190000" },
  { name: "장수군", slug: "jangsu", regionSlug: "jeonbuk", apiCode: "4180000" },
  { name: "전주시", slug: "jeonju", regionSlug: "jeonbuk", apiCode: "4120000" },
  { name: "정읍시", slug: "jeongeup", regionSlug: "jeonbuk", apiCode: "4160000" },
  { name: "진안군", slug: "jinan", regionSlug: "jeonbuk", apiCode: "4180000" },

  // ===== 전라남도 (22개 시/군) =====
  { name: "강진군", slug: "gangjin", regionSlug: "jeonnam", apiCode: "4290000" },
  { name: "고흥군", slug: "goheung", regionSlug: "jeonnam", apiCode: "4270000" },
  { name: "곡성군", slug: "gokseong", regionSlug: "jeonnam", apiCode: "4240000" },
  { name: "광양시", slug: "gwangyang", regionSlug: "jeonnam", apiCode: "4230000" },
  { name: "구례군", slug: "gurye", regionSlug: "jeonnam", apiCode: "4240000" },
  { name: "나주시", slug: "naju", regionSlug: "jeonnam", apiCode: "4220000" },
  { name: "담양군", slug: "damyang", regionSlug: "jeonnam", apiCode: "4240000" },
  { name: "목포시", slug: "mokpo", regionSlug: "jeonnam", apiCode: "4210000" },
  { name: "무안군", slug: "muan", regionSlug: "jeonnam", apiCode: "4310000" },
  { name: "보성군", slug: "boseong", regionSlug: "jeonnam", apiCode: "4270000" },
  { name: "순천시", slug: "suncheon", regionSlug: "jeonnam", apiCode: "4220000" },
  { name: "신안군", slug: "sinan", regionSlug: "jeonnam", apiCode: "4320000" },
  { name: "여수시", slug: "yeosu", regionSlug: "jeonnam", apiCode: "4220000" },
  { name: "영광군", slug: "yeonggwang", regionSlug: "jeonnam", apiCode: "4310000" },
  { name: "영암군", slug: "yeongam", regionSlug: "jeonnam", apiCode: "4300000" },
  { name: "완도군", slug: "wando", regionSlug: "jeonnam", apiCode: "4300000" },
  { name: "장성군", slug: "jangseong", regionSlug: "jeonnam", apiCode: "4310000" },
  { name: "장흥군", slug: "jangheung", regionSlug: "jeonnam", apiCode: "4280000" },
  { name: "진도군", slug: "jindo", regionSlug: "jeonnam", apiCode: "4320000" },
  { name: "함평군", slug: "hampyeong", regionSlug: "jeonnam", apiCode: "4310000" },
  { name: "해남군", slug: "haenam", regionSlug: "jeonnam", apiCode: "4290000" },
  { name: "화순군", slug: "hwasun", regionSlug: "jeonnam", apiCode: "4260000" },

  // ===== 경상북도 (23개 시/군) =====
  { name: "경산시", slug: "gyeongsan", regionSlug: "gyeongbuk", apiCode: "4410000" },
  { name: "경주시", slug: "gyeongju", regionSlug: "gyeongbuk", apiCode: "4340000" },
  { name: "고령군", slug: "goryeong", regionSlug: "gyeongbuk", apiCode: "4430000" },
  { name: "구미시", slug: "gumi", regionSlug: "gyeongbuk", apiCode: "4370000" },
  { name: "김천시", slug: "gimcheon", regionSlug: "gyeongbuk", apiCode: "4350000" },
  { name: "문경시", slug: "mungyeong", regionSlug: "gyeongbuk", apiCode: "4390000" },
  { name: "봉화군", slug: "bonghwa", regionSlug: "gyeongbuk", apiCode: "4460000" },
  { name: "상주시", slug: "sangju", regionSlug: "gyeongbuk", apiCode: "4380000" },
  { name: "성주군", slug: "seongju", regionSlug: "gyeongbuk", apiCode: "4430000" },
  { name: "안동시", slug: "andong", regionSlug: "gyeongbuk", apiCode: "4360000" },
  { name: "영덕군", slug: "yeongdeok", regionSlug: "gyeongbuk", apiCode: "4450000" },
  { name: "영양군", slug: "yeongyang", regionSlug: "gyeongbuk", apiCode: "4450000" },
  { name: "영주시", slug: "yeongju", regionSlug: "gyeongbuk", apiCode: "4390000" },
  { name: "영천시", slug: "yeongcheon", regionSlug: "gyeongbuk", apiCode: "4400000" },
  { name: "예천군", slug: "yecheon", regionSlug: "gyeongbuk", apiCode: "4460000" },
  { name: "울릉군", slug: "ulleung", regionSlug: "gyeongbuk", apiCode: "4470000" },
  { name: "울진군", slug: "uljin", regionSlug: "gyeongbuk", apiCode: "4460000" },
  { name: "의성군", slug: "uiseong", regionSlug: "gyeongbuk", apiCode: "4420000" },
  { name: "청도군", slug: "cheongdo", regionSlug: "gyeongbuk", apiCode: "4430000" },
  { name: "청송군", slug: "cheongsong", regionSlug: "gyeongbuk", apiCode: "4440000" },
  { name: "칠곡군", slug: "chilgok", regionSlug: "gyeongbuk", apiCode: "4430000" },
  { name: "포항시", slug: "pohang", regionSlug: "gyeongbuk", apiCode: "4330000" },
  { name: "고령군", slug: "goryeong", regionSlug: "gyeongbuk", apiCode: "4430000" },

  // ===== 경상남도 (18개 시/군) =====
  { name: "거제시", slug: "geoje", regionSlug: "gyeongnam", apiCode: "4560000" },
  { name: "거창군", slug: "geochang", regionSlug: "gyeongnam", apiCode: "4590000" },
  { name: "고성군", slug: "gsngoseong", regionSlug: "gyeongnam", apiCode: "4570000" },
  { name: "김해시", slug: "gimhae", regionSlug: "gyeongnam", apiCode: "4530000" },
  { name: "남해군", slug: "namhae", regionSlug: "gyeongnam", apiCode: "4570000" },
  { name: "밀양시", slug: "miryang", regionSlug: "gyeongnam", apiCode: "4540000" },
  { name: "사천시", slug: "sacheon", regionSlug: "gyeongnam", apiCode: "4510000" },
  { name: "산청군", slug: "sancheong", regionSlug: "gyeongnam", apiCode: "4580000" },
  { name: "양산시", slug: "yangsan", regionSlug: "gyeongnam", apiCode: "4550000" },
  { name: "의령군", slug: "uiryeong", regionSlug: "gyeongnam", apiCode: "4560000" },
  { name: "진주시", slug: "jinju", regionSlug: "gyeongnam", apiCode: "4500000" },
  { name: "창녕군", slug: "changnyeong", regionSlug: "gyeongnam", apiCode: "4560000" },
  { name: "창원시", slug: "changwon", regionSlug: "gyeongnam", apiCode: "4490000" },
  { name: "통영시", slug: "tongyeong", regionSlug: "gyeongnam", apiCode: "4510000" },
  { name: "하동군", slug: "hadong", regionSlug: "gyeongnam", apiCode: "4580000" },
  { name: "함안군", slug: "haman", regionSlug: "gyeongnam", apiCode: "4560000" },
  { name: "함양군", slug: "hamyang", regionSlug: "gyeongnam", apiCode: "4580000" },
  { name: "합천군", slug: "hapcheon", regionSlug: "gyeongnam", apiCode: "4590000" },

  // ===== 제주특별자치도 (2개 시) =====
  { name: "제주시", slug: "jejusi", regionSlug: "jeju", apiCode: "4610000" },
  { name: "서귀포시", slug: "seogwipo", regionSlug: "jeju", apiCode: "4620000" },
];

// Helper functions
export function getRegionBySlug(slug: string): RegionMapping | undefined {
  return REGIONS.find((r) => r.slug === slug);
}

export function getDistrictBySlug(
  regionSlug: string,
  districtSlug: string
): DistrictMapping | undefined {
  return DISTRICTS.find(
    (d) => d.regionSlug === regionSlug && d.slug === districtSlug
  );
}

export function getDistrictsByRegion(regionSlug: string): DistrictMapping[] {
  return DISTRICTS.filter((d) => d.regionSlug === regionSlug);
}

// 시/도 축약명. 이름이 겹치는 구군을 구분해 표시할 때만 사용한다.
const REGION_SHORT_NAMES: Record<string, string> = {
  seoul: "서울",
  busan: "부산",
  daegu: "대구",
  incheon: "인천",
  gwangju: "광주",
  daejeon: "대전",
  ulsan: "울산",
  sejong: "세종",
  gyeonggi: "경기",
  gangwon: "강원",
  chungbuk: "충북",
  chungnam: "충남",
  jeonbuk: "전북",
  jeonnam: "전남",
  gyeongbuk: "경북",
  gyeongnam: "경남",
  jeju: "제주",
};

// 전국에서 이름이 2곳 이상 겹치는 구군 이름 집합.
// (중구/동구/서구/남구/북구/강서구/고성군 — 29개 페이지)
// regionSlug+slug 기준으로 먼저 중복 제거해 같은 구군의 중복 등록을 오탐하지 않는다.
const DUPLICATE_DISTRICT_NAMES: ReadonlySet<string> = (() => {
  const seen = new Set<string>();
  const counts = new Map<string, number>();
  for (const d of DISTRICTS) {
    const key = `${d.regionSlug}/${d.slug}`;
    if (seen.has(key)) continue;
    seen.add(key);
    counts.set(d.name, (counts.get(d.name) ?? 0) + 1);
  }
  return new Set(
    [...counts].filter(([, n]) => n > 1).map(([name]) => name)
  );
})();

/**
 * 화면·title·FAQ에 공통으로 쓰는 구군 표시명.
 * 이름이 겹치는 구군에만 시/도 축약명을 붙인다. ("부산 동구", "강원 고성군")
 * 겹치지 않는 구군은 기존 표기를 그대로 유지한다. ("강남구")
 */
export function getDistrictDisplayName(
  regionSlug: string,
  districtName: string
): string {
  if (!DUPLICATE_DISTRICT_NAMES.has(districtName)) return districtName;
  const short = REGION_SHORT_NAMES[regionSlug];
  return short ? `${short} ${districtName}` : districtName;
}

// ────────────────────────────────────────────────────────────────────────
// 인천 2026 행정구역 개편 (2026-07-01 시행) — 사용자 표시 SSOT
//
// /incheon/icjunggu 같은 URL은 "현재의 어떤 행정구" 페이지가 아니라
// 개편 이전 행정구 영역을 보존하는 compatibility bucket이다. URL은 호환성
// 자산이라 바꾸지 않고, 사용자에게 보이는 이름만 현재 행정구역에 맞춘다.
//
// collector의 LEGACY_ROUTE_DISTRICT_MAP과 역할이 다르다.
//   collector : 데이터가 어느 legacy bucket으로 들어가는가
//   여기      : 그 legacy bucket을 사용자에게 어떻게 설명하는가
// 둘을 섞지 않는다.
//
// 매장 주소는 공공데이터가 제공하는 원문을 그대로 쓴다. 표시명 정책과
// 주소 문자열 정책은 별개다. 주소는 사용자가 찾아갈 때 쓰는 실용 정보다.
//
// 지금은 인천 3개만 명시한다. 전국 행정개편 프레임워크를 만들지 않는다.
// ────────────────────────────────────────────────────────────────────────
export interface LegacyDistrictDisplay {
  /** title·H1·meta·FAQ 질문용. 현재 행정구역 + 옛 이름 병기 */
  longLabel: string;
  /** breadcrumb용. 시도가 문맥상 자명하므로 축약 */
  shortLabel: string;
  /** 지역 선택 카드의 주 label */
  selectorMain: string;
  /** 지역 선택 카드의 보조 문구 */
  selectorLegacy: string;
  /**
   * FAQ 답변·본문에서 "이 페이지가 다루는 범위"를 가리킬 때 쓴다.
   * longLabel을 답변에 쓰면 "제물포구·영종구에는 82곳"처럼 읽혀
   * 제물포구 전체와 영종구 전체의 합으로 오해된다.
   */
  scopeLabel: string;
  /** 행정구역 개편 안내. 페이지별 실제 coverage에 맞춰 다르게 쓴다 */
  notice: string;
}

const INCHEON_LEGACY_DISPLAY: Record<string, LegacyDistrictDisplay> = {
  icjunggu: {
    longLabel: "제물포구·영종구 (옛 인천 중구)",
    shortLabel: "제물포구·영종구 (옛 중구)",
    selectorMain: "제물포구·영종구",
    selectorLegacy: "옛 중구",
    scopeLabel: "옛 인천 중구 지역",
    notice:
      "이 페이지는 2026년 7월 행정구역 개편 이전 인천 중구 지역을 기준으로 묶은 판매처 정보입니다. 현재 이 지역은 제물포구와 영종구에 속합니다. 매장 주소는 공공데이터에 제공된 주소를 그대로 표시합니다.",
  },
  icdonggu: {
    longLabel: "제물포구 (옛 인천 동구)",
    shortLabel: "제물포구 (옛 동구)",
    selectorMain: "제물포구",
    selectorLegacy: "옛 동구",
    scopeLabel: "옛 인천 동구 지역",
    notice:
      "이 페이지는 2026년 7월 행정구역 개편 이전 인천 동구 지역을 기준으로 묶은 판매처 정보입니다. 현재 이 지역은 제물포구에 속합니다. 매장 주소는 공공데이터에 제공된 주소를 그대로 표시합니다.",
  },
  icseogu: {
    longLabel: "서해구·검단구 (옛 인천 서구)",
    shortLabel: "서해구·검단구 (옛 서구)",
    selectorMain: "서해구·검단구",
    selectorLegacy: "옛 서구",
    scopeLabel: "옛 인천 서구 지역",
    notice:
      "이 페이지는 2026년 7월 행정구역 개편 이전 인천 서구 지역을 기준으로 묶은 판매처 정보입니다. 현재 이 지역은 서해구와 검단구로 나뉘었습니다. 매장 주소는 공공데이터에 제공된 주소를 그대로 표시합니다.",
  },
};

/** 개편으로 표시명이 달라진 legacy bucket이면 표시 정보를, 아니면 null. */
export function getLegacyDisplay(
  regionSlug: string,
  districtSlug: string
): LegacyDistrictDisplay | null {
  if (regionSlug !== "incheon") return null;
  return INCHEON_LEGACY_DISPLAY[districtSlug] ?? null;
}

// ────────────────────────────────────────────────────────────────────────
// 전남·광주 통합 (2026-07-01 시행) — 시도 표시 SSOT
//
// 전남광주통합특별시 설치 및 지원에 관한 특별법
//   2026-03-05 제정 / 2026-07-01 시행
//   제7조에 법정 약칭 "광주특별시" 명시
//   종전 광주광역시·전라남도는 폐지
//
// /gwangju 와 /jeonnam 은 통합특별시 안의 옛 광주 영역·옛 전남 영역을
// 보존하는 compatibility region이다. 통합특별시 아래에는 27개 구·시군이
// 평평하게 있고 이 둘을 묶는 현재 행정 단위는 없다. 그래서 "광주 지역"
// 같은 준행정명을 만들지 않고, 법정 약칭 + 폐지된 옛 시도명을 병기한다.
//
// 인천과 다른 점: 하위 27개 구·시군 이름은 그대로 유효하다. 북구는 여전히
// 북구고 보성군은 여전히 보성군이다. 따라서 district title/H1은 바꾸지 않고
// 시도명이 드러나는 surface만 고친다.
//
// REGIONS.name(canonical identity)은 건드리지 않는다. collector의
// REGION_NAME_TO_SLUG와 이름 체계를 공유하고, REGION_SHORT_NAMES를 바꾸면
// 중복 구군명 4개(동구·서구·남구·북구)의 title까지 흔들린다.
// ────────────────────────────────────────────────────────────────────────
export interface LegacyRegionDisplay {
  /** region page의 title·H1·meta·FAQ 질문 */
  longLabel: string;
  /** breadcrumb 상위 노드 */
  shortLabel: string;
  /** 내부링크 anchor·섹션 제목·FAQ 답변. 짧아야 하는 곳 */
  currentLabel: string;
  /** RegionGrid 카드의 보조 문구 */
  legacyLabel: string;
}

const LEGACY_REGION_DISPLAY: Record<string, LegacyRegionDisplay> = {
  gwangju: {
    longLabel: "광주특별시 (옛 광주광역시)",
    shortLabel: "광주특별시 (옛 광주)",
    currentLabel: "광주특별시",
    legacyLabel: "옛 광주광역시",
  },
  jeonnam: {
    longLabel: "광주특별시 (옛 전라남도)",
    shortLabel: "광주특별시 (옛 전남)",
    currentLabel: "광주특별시",
    legacyLabel: "옛 전라남도",
  },
};

/** 통합으로 시도명이 바뀐 compatibility region이면 표시 정보를, 아니면 null. */
export function getRegionDisplay(
  regionSlug: string
): LegacyRegionDisplay | null {
  return LEGACY_REGION_DISPLAY[regionSlug] ?? null;
}
