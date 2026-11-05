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
