// Shared data for the homepage and archive page.
// Keep department codes consistent with the codes in each record's departmentCode.
const departments = [
  { name: "Agriculture, Supply & Prices Department", short: "Agriculture & Supply", code: "ASP" },
  { name: "Auqaf Religious Affairs Zakat & Ushr Department", short: "Auqaf, Religious Affairs & Zakat", code: "ARAZU" },
  { name: "Board of Revenue (BOR)", short: "Board of Revenue", code: "BOR" },
  { name: "Chief Minister's Secretariat & Inspection Team", short: "CM Secretariat", code: "CMSIT" },
  { name: "College Education Department", short: "College Education", code: "CED" },
  { name: "Cooperative Department", short: "Cooperative", code: "COOP" },
  { name: "Culture, Tourism & Antiquities Department", short: "Culture & Tourism", code: "CTA" },
  { name: "Department of Empowerment of Persons with Disabilities", short: "Empowerment of Persons with Disabilities", code: "DEPD" },
  { name: "Energy Department", short: "Energy", code: "ENERGY" },
  { name: "Enquiries & Anti-Corruption Establishment", short: "Anti-Corruption Establishment", code: "EACE" },
  { name: "Environment, Climate Change & Coastal Development Department", short: "Environment & Climate Change", code: "ECCD" },
  { name: "Excise, Taxation & Narcotics Control Department", short: "Excise & Taxation", code: "ETNC" },
  { name: "Finance Department", short: "Finance", code: "FIN" },
  { name: "Food Department & Sindh Food Authority", short: "Food & Food Authority", code: "FD-SFA" },
  { name: "Forest & Wildlife Department", short: "Forest & Wildlife", code: "FW" },
  { name: "Health Department", short: "Health", code: "HEALTH" },
  { name: "Home Department & Sindh Police", short: "Home & Police", code: "HOME-POL" },
  { name: "Human Rights Department", short: "Human Rights", code: "HRD" },
  { name: "Industries & Commerce Department", short: "Industries & Commerce", code: "IC" },
  { name: "Information Department", short: "Information", code: "INFO" },
  { name: "Inter Provincial Coordination Department", short: "Inter Provincial Coordination", code: "IPCD" },
  { name: "Investment Department", short: "Investment", code: "INVEST" },
  { name: "Irrigation Department", short: "Irrigation", code: "IRR" },
  { name: "Labour & Human Resources Department", short: "Labour & Human Resources", code: "LHR" },
  { name: "Law Department & Prosecutor General", short: "Law & Prosecution", code: "LDPG" },
  { name: "Livestock & Fisheries Department", short: "Livestock & Fisheries", code: "LF" },
  { name: "Local Government & Housing Town Planning Department", short: "Local Government & Housing", code: "LGHTP" },
  { name: "Mines & Mineral Development Department", short: "Mines & Minerals", code: "MMD" },
  { name: "Minorities Affairs Department", short: "Minorities Affairs", code: "MA" },
  { name: "Planning & Development Department", short: "Planning & Development", code: "P&D" },
  { name: "Population Welfare Department", short: "Population Welfare", code: "PWD" },
  { name: "Public Health Engineering & Rural Development Department", short: "Public Health Engineering", code: "PHERDD" },
  { name: "Rehabilitation Department", short: "Rehabilitation", code: "REHAB" },
  { name: "School Education & Literacy Department", short: "School Education & Literacy", code: "SELD" },
  { name: "Science & Information Technology Department", short: "Science & Information Technology", code: "SIT" },
  { name: "Services, General Administration & Coordination Department (SGA&CD)", short: "Services & General Administration", code: "SGA-CD" },
  { name: "Sindh Higher Education Commission (Sindh HEC)", short: "Sindh HEC", code: "SHEC" },
  { name: "Social Welfare Department", short: "Social Welfare", code: "SWD" },
  { name: "Sports & Youth Affairs Department", short: "Sports & Youth Affairs", code: "SYA" },
  { name: "Transport & Mass Transit Department", short: "Transport & Mass Transit", code: "TMT" },
  { name: "Universities & Boards Department", short: "Universities & Boards", code: "UBD" },
  { name: "Women Development Department", short: "Women Development", code: "WDD" },
  { name: "Works & Services Department", short: "Works & Services", code: "W&S" }
];

// Official portal listing data.
// Add new source-backed entries here; do not use portal listing numbers as document references.
const records = [
  {
    "portalListingNumber": 1,
    "date": "2026-09-18",
    "title": "Hosting of Government Websites in Pakistan",
    "type": "Notification",
    "departmentCode": null,
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/EKqqtUqbPsT2rzrihJBD1SKaTTULTY8iJ6GAz0qC.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 2,
    "date": "2026-07-04",
    "title": "SACM Seher Gul Bhatti",
    "type": "Notification",
    "departmentCode": null,
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/86dsQGIzx6TEL44K6s6omIhBiQAIhqqXXU47f5Ak.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 3,
    "date": "2026-07-14",
    "title": "Advisory",
    "type": "Advisory",
    "departmentCode": null,
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/DbGhPMQtBJt1JOq52LyFtLcmeNZT0ncrxDZ4TfWC.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 4,
    "date": "2026-07-14",
    "title": "Advisory",
    "type": "Advisory",
    "departmentCode": null,
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/M84iJKsEcTGj51hnKADLK5K7xPyFejWeelyESCi0.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 5,
    "date": "2026-03-02",
    "title": "Holidays for Hindu Community for the Occasion of Dulhandi and Holi",
    "type": "Notification",
    "departmentCode": null,
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/Vpw4dnkKmZwHMYjMtcwJNt4v25ijmfXkhm8fahxo.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 7,
    "date": "2026-01-28",
    "title": "CYBER SECURITY ADVISORY ON ANDROID ZERO-DAY EXPLOIT IMMEDIATE ACTION",
    "type": "Advisory",
    "departmentCode": null,
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/E2QyNbOlj1rEnKDpqVw7JlDP0UnjM4HiW1igdL4U.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 8,
    "date": "2025-12-19",
    "title": "Cyber Security Advisory on Prevention Against Exploitation of Video Conferencing Applications (Zoom, Google Meet etc)",
    "type": "Advisory",
    "departmentCode": null,
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/91KSd8M00WHlXe2XWYRwtj5fVedPprKvFEcyM6cs.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 9,
    "date": "2025-12-17",
    "title": "Cyber Security Advisory on Risks Associated With Smart / Internet-Enabled IPTV Devices in Sensitive Premises Immediate Mitigation Measures",
    "type": "Advisory",
    "departmentCode": null,
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/gwaa6YnZGMHo6OewaO59AJAmEanfZ4zVcf0YgWg6.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 10,
    "date": "2025-11-13",
    "title": "Cyber Security Advisory on Immediate Mitigation of Multiple Critical Vulnerabilities",
    "type": "Advisory",
    "departmentCode": null,
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/TwZbR1JIFggsYiahHppGvjOEzVasz1tE8Ar2bQQC.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 11,
    "date": "2025-11-13",
    "title": "Cyber Security Advisory on Risks of Hosting Government Email Infrastructure Outside National Jurisdiction",
    "type": "Advisory",
    "departmentCode": null,
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/YxH9l13VG7LvTHt3PnkiMNwiDWpX0ihLe6bXGpsK.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 13,
    "date": "2025-09-26",
    "title": "Mr. Muhammad Ismail Rahoo",
    "type": "Notification",
    "departmentCode": null,
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/kNJvWyfI1e96lAK8AAeGe2O4hGlyZwyj4w1dGvXA.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 14,
    "date": "2025-09-26",
    "title": "Allocate and Re allocate portfolios of Minister",
    "type": "Notification",
    "departmentCode": null,
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/NUBVPC7Mf2Xqiv8Ko4orXyRM0KDYMeMxBTNuDyUC.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 15,
    "date": "2025-08-08",
    "title": "Cyber Security Advisory -Revamping CS Postures of Government Websites",
    "type": "Advisory",
    "departmentCode": null,
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/tvQLHxleLzEm25SLnY41DcNc9XO6ksqu3NInaVaD.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 16,
    "date": "2025-08-07",
    "title": "IRRIGATION DEPARTMENT ORDER",
    "type": "Order",
    "departmentCode": "IRR",
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/AQTZAGE1ut3sOfOLd1pfyyQD5byktE8LHXHXury1.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 17,
    "date": "2025-08-04",
    "title": "CYBER SECURITY ADVISORY -IVANTI ZERO DAY ATTACK ON TELECOM IT NETWORK",
    "type": "Advisory",
    "departmentCode": null,
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/s4hVYcCYTwnH2kHUFURlk6u5eeIGlOnRGu6fjti5.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 18,
    "date": "2025-07-11",
    "title": "Advisory",
    "type": "Advisory",
    "departmentCode": null,
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/I9lOUpkcrcER8s13gchRUDnjKa7kv6mQO8XKIqlS.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 19,
    "date": "2025-07-11",
    "title": "Advisory",
    "type": "Advisory",
    "departmentCode": null,
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/erumRCNOtWxObnr7hKhV3yaj5hV0W0kspE6ydIGX.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 20,
    "date": "2025-07-11",
    "title": "Advisory",
    "type": "Advisory",
    "departmentCode": null,
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/NbyZkt5RJNNSoqQdNWkV9TBYtORzNFCIS6pBQKIy.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 21,
    "date": "2025-07-11",
    "title": "Advisory",
    "type": "Advisory",
    "departmentCode": null,
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/Rf6VocBpvvb1XdxhTMKqPPMejgnDeCnDvKamujhK.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 22,
    "date": "2025-07-10",
    "title": "Advisory",
    "type": "Advisory",
    "departmentCode": null,
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/RsAy4INAhviDaEfAS0tIQ9EDIXEnsYaTyj2yYkSL.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 23,
    "date": "2025-07-10",
    "title": "Advisory",
    "type": "Advisory",
    "departmentCode": null,
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/7Z0eo3GDDwHdwrH0lSwPROqetq9ivUFe51V1mnzF.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 24,
    "date": "2025-06-23",
    "title": "Energy Department",
    "type": "Notification",
    "departmentCode": "ENERGY",
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/68o4x8AUg1I3xgiDA0pfKxCCKVj34n5h9tAG358x.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 25,
    "date": "2025-06-23",
    "title": "Energy Department",
    "type": "Notification",
    "departmentCode": "ENERGY",
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/GBSHc96r1ESVEfos8iBVEhY7T65tIM4vVmNE6Hx7.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 26,
    "date": "2025-05-27",
    "title": "Cyber Security Advisory Fortinet Farewell",
    "type": "Advisory",
    "departmentCode": null,
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/Qso0DAjyl2N7X4PmhHgHoTWz8d8YbR3gHnXOoEP3.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 27,
    "date": "2025-05-27",
    "title": "Cyber Security Advisory Malicious Apps found on Google Play Store",
    "type": "Advisory",
    "departmentCode": null,
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/2tgvRuFU0BAxiFXQaLQ6d6tfjmhUh6I72yUlmjnu.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 28,
    "date": "2025-05-27",
    "title": "Cyber Security Advisory Apple Patches Actively Exploited Web-kit Zero Day",
    "type": "Advisory",
    "departmentCode": null,
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/vhwXShZd83cmLGQhivZEfiyf8wYo8Vj1iWA0LeOm.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 29,
    "date": "2025-03-24",
    "title": "Promotion",
    "type": "Notification",
    "departmentCode": null,
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/onT7XxArZeXgFYjwqLjEg0cIwoHIWqFQkpWIONzN.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 30,
    "date": "2025-02-25",
    "title": "Critical Information Infrastructure Protection",
    "type": "Notification",
    "departmentCode": null,
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/q0giNQ04xecwAd3O4j0Ek4bdpCuYDQq8UpQV1Yhw.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 31,
    "date": "2025-02-25",
    "title": "National Computer Emergency Response Team",
    "type": "Notification",
    "departmentCode": null,
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/dhRz7I11vmxmsoNZdcMLddmNLtry9DIusVgd2N8y.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 32,
    "date": "2025-01-31",
    "title": "Cyber Security Advisory",
    "type": "Advisory",
    "departmentCode": null,
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/1m6J7NFR8a3EGRhwEFhrn2qms5DvYHAwuUZUE6hK.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 33,
    "date": "2025-01-23",
    "title": "Reply of Awarness Drive about Benami Transcation",
    "type": "Notification",
    "departmentCode": null,
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/npJyTdhGr3ZJWoXADd81pdQCK2qlWSQfS31HwGL5.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 34,
    "date": "2025-01-23",
    "title": "Awarness Drive about Benami Transication",
    "type": "Notification",
    "departmentCode": null,
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/M6ZJVZ2We2ffgTSbzKvoFDDOwYGPqwmimIubxKyW.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 35,
    "date": "2025-01-13",
    "title": "Appointment of Spokesperson",
    "type": "Notification",
    "departmentCode": null,
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/m6SZan2cRJxE7P99oCyewfrxobZAnwxTE8yRWG3T.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 36,
    "date": "2025-01-13",
    "title": "Appointment of Special Assistant to CM Sindh",
    "type": "Notification",
    "departmentCode": null,
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/3XQobJRfEyd2S3PdVLuZospS0j7Qft3BuBgZWXGC.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 37,
    "date": "2025-01-03",
    "title": "Amendments in the Sindh Government Rules of Business 1986",
    "type": "Notification",
    "departmentCode": "SGA-CD",
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/Vb12RChHGzU3T1FUuqpXkK2oRY5fSZntzKEXZEfu.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 38,
    "date": "2025-01-09",
    "title": "EXPRESSION OF INTEREST",
    "type": "Notice",
    "departmentCode": null,
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/2FhFjVb5nFWwHXxZS2cFmgxru44CJtvnNeCjsRcy.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 39,
    "date": "2025-01-02",
    "title": "Notification",
    "type": "Notification",
    "departmentCode": null,
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/zyklgpBFsbWK2qO02D0LgqGzDCbZUkqNrLFK7TvF.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 40,
    "date": "2024-12-19",
    "title": "Sindh Civil Servants Act 1973",
    "type": "Legislation",
    "departmentCode": null,
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/8Wh8bi1ZLKr61rnfZ9l7xFuFRv8VVAMM4FLYuHGD.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 41,
    "date": "2024-11-26",
    "title": "Cyber Security Implications of wearable devices",
    "type": "Notification",
    "departmentCode": null,
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/CUp49cULvVZnh0ycxXP2nbeJ1aw4KC9sZs1hw2R9.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 42,
    "date": "2024-11-26",
    "title": "Cyber Security Advisory Strengthening \" Know your Client KYC process for cyber security compliance and threat mitigation",
    "type": "Advisory",
    "departmentCode": null,
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/JhqAuLHR5XuhkFc3mghVLvYR3fadCMrJHZm1j4iA.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 43,
    "date": "2024-11-26",
    "title": "Cyber Security Advisory Securing Sensitive Digital Documents Confidential Files",
    "type": "Advisory",
    "departmentCode": null,
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/kBU6WAiLS1CD27Ui6ZZOywE3a51YKEWrL3Xyqep1.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 44,
    "date": "2024-08-27",
    "title": "Advisory",
    "type": "Advisory",
    "departmentCode": null,
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/VSdaNnl7oe4xxOsTpyeJ8RpjBH8Wnp0u02BoRP3b.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 45,
    "date": "2024-08-13",
    "title": "Cyber Security Advisory",
    "type": "Advisory",
    "departmentCode": null,
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/QzdF8Z4eqDT8TH3HElzk65LkhHbW0k6q00ehmFN8.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 46,
    "date": "2024-05-24",
    "title": "Blacklisted",
    "type": "Notification",
    "departmentCode": null,
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/eWMuxAxiTDNgSKTpCMo4pyfEmj9Fri5pB0ZYwrcc.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 47,
    "date": "2024-05-12",
    "title": "Cabinet Committee on Finance",
    "type": "Notification",
    "departmentCode": "FIN",
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/WqMOjIgVuaafrIMmnOwop8O1LKUvke6G90odjDXM.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 48,
    "date": "2024-03-06",
    "title": "INFORMATION SCIENCE & TECHNOLOGY DEPARTMENT ADVISORY",
    "type": "Advisory",
    "departmentCode": null,
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/RnIKYfzovNTGcp0En65dDLQSrLwb6gPqmiVq3Hf8.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 49,
    "date": "2023-08-21",
    "title": "Caretaker Minister's Order Notification",
    "type": "Order",
    "departmentCode": "SGA-CD",
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/HryZVQXNl6QwHEpzgHrGOpBuboOLirRWuq1r0ohM.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 50,
    "date": "2023-05-19",
    "title": "Serives General Administration & coordination Department",
    "type": "Notification",
    "departmentCode": null,
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/lByNMw8LO0xXHdp1FH0465mFFQ3hdGKQSc29iz5j.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 51,
    "date": "2022-10-06",
    "title": "Government of Sindh , Services General Administration and Coordination Department",
    "type": "Notification",
    "departmentCode": "SGA-CD",
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/2JtBqKpJ8DwAV4YopbbXY8jPqPQf9bUI8FKpBXJB.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 52,
    "date": "2022-05-20",
    "title": "Services General Administration & Coordination Department",
    "type": "Notification",
    "departmentCode": "SGA-CD",
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/eyXQ289ihxGGjoiaxY6RdiyWAtI34it0a9dPnL6e.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 53,
    "date": "2022-05-20",
    "title": "Services General Administration & Coordination Department",
    "type": "Notification",
    "departmentCode": "SGA-CD",
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/7gRVJd6FiEHrA8elv9cZqTIGMH1w6L54qZrrwM8r.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 54,
    "date": "2021-11-10",
    "title": "GOVERNMENT OF SINDH, SERVICES GENERAL ADMINISTRATION & COORDINATION DEPARTMENT",
    "type": "Notification",
    "departmentCode": "SGA-CD",
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/GVJps0jIandvqxl3NeB8i6uTZhiWg4ur5CqBEOye.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 55,
    "date": "2021-08-10",
    "title": "GOVERNMENT OF SINDH, SERVICES GENERAL ADMINISTRATION & COORDINATION DEPARTMENT CABINET SECTION (UPDATED)",
    "type": "Notification",
    "departmentCode": "SGA-CD",
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/h2pV26oHPEytPUjfuDBB3VtNWx8sDKe3JDgxdLjR.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 56,
    "date": "2019-03-11",
    "title": "GOVERNMENT OF SINDH, SERVICES GENERAL ADMINISTRATION & COORDINATION DEPARTMENT",
    "type": "Notification",
    "departmentCode": "SGA-CD",
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/wWDJhcvak1INBlUxJO6IG9XrOqFyORS7fugcRgoQ.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  },
  {
    "portalListingNumber": 57,
    "date": "2019-03-08",
    "title": "GOVERNMENT OF SINDH, ENERGY DEPARTMENT",
    "type": "Notification",
    "departmentCode": "ENERGY",
    "pdfUrl": "https://www.sindh.gov.pk/storage/notification/2EJP6Iiy05zWRp6658jSHPLSTFwMx15KHBVgl8Bi.pdf",
    "sourceUrl": "https://www.sindh.gov.pk/notifications?show=notification"
  }
];

// Used only if a record's department is not present in the department list.
const unspecifiedDepartment = {
  name: "Government of Sindh (department not specified in listing)",
  short: "Department not specified",
  code: "UNSPECIFIED",
};

// Give every listing a searchable project ID and a label for its Government portal row.
for (const record of records) {
  const department = departments.find((item) => item.code === record.departmentCode) || unspecifiedDepartment;
  record.department = department.name;
  record.shortDepartment = department.short;
  record.id = `GOS-PORTAL-${String(record.portalListingNumber).padStart(3, "0")}`;
  record.archiveReference = `SGNIA-ARCH-${String(record.portalListingNumber).padStart(3, "0")}`;
  record.officialReference = null;
  record.status = "Official Government of Sindh portal listing";
}

// Department assignments confirmed from the title or the issuing department in the PDF.
// Keys are portal listing numbers; values must match a code in the departments list above.
const departmentOverrides = {
  1: "SIT",
  2: "SGA-CD",
  3: "SIT",
  4: "SIT",
  5: "SGA-CD",
  7: "SIT",
  8: "SIT",
  9: "SIT",
  10: "SIT",
  11: "SIT",
  13: "SGA-CD",
  14: "SGA-CD",
  15: "SIT",
  17: "SIT",
  18: "SIT",
  19: "SIT",
  20: "SIT",
  21: "SIT",
  22: "SIT",
  23: "SIT",
  26: "SIT",
  27: "SIT",
  28: "SIT",
  29: "SGA-CD",
  30: "SIT",
  31: "SIT",
  32: "SIT",
  33: "SIT",
  34: "FIN",
  35: "SGA-CD",
  36: "SGA-CD",
  38: "SGA-CD",
  39: "ENERGY",
  40: "SGA-CD",
  41: "SIT",
  42: "SIT",
  43: "SIT",
  44: "SIT",
  45: "SIT",
  46: "SGA-CD",
  48: "SIT",
  50: "SGA-CD",
};

// Official reference numbers transcribed from readable source PDFs.
// Leave a listing out rather than guessing if its official number cannot be read.
const officialReferences = {
  2: "SOVI(SGA&CD)4(24)/2026",
  4: "DG-II/CERT/4/124/2023/P-I",
  5: "CTC(SGA&CD)27(2)2010",
  13: "SOVI(SGA&CD)2(1)/2024",
  14: "SOVI(SGA&CD)2(1)/2024",
  29: "SOII(SGA&CD)7-1/2025",
  35: "SOVI(SGA&CD)5(1)/2025",
  36: "SOVI(SGA&CD)4(1)/2025",
  38: "SO(T)(SGA&CD)77/2024",
  39: "ED/SO(Admn)/12-6/AEI/2014(13)",
  40: "SORI(SGA&CD)2-25/2024",
  44: "DG-II/Cyber Advisory/4/111/2023",
};

// Apply verified overrides and refresh the department display fields.
for (const record of records) {
  const departmentCode = departmentOverrides[record.portalListingNumber] || record.departmentCode;
  const department = departments.find((item) => item.code === departmentCode) || unspecifiedDepartment;
  record.departmentCode = departmentCode;
  record.department = department.name;
  record.shortDepartment = department.short;
  record.officialReference = officialReferences[record.portalListingNumber] || null;
}
