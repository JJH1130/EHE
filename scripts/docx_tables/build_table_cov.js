const {
  Document, Packer, Paragraph, Table, TableRow, TableCell, TextRun,
  WidthType, AlignmentType, VerticalAlign, BorderStyle,
} = require("docx");

const FONT = "Arial";
const TABLE_W = 9360;
const NONE = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const THIN = { style: BorderStyle.SINGLE, size: 4, color: "000000" };
const THICK = { style: BorderStyle.SINGLE, size: 8, color: "000000" };

function cellBorders({ top = NONE, bottom = NONE } = {}) {
  return { top, bottom, left: NONE, right: NONE };
}

function cell(text, { align = AlignmentType.CENTER, width, bold = false, top, bottom, rowSpan, columnSpan, italics = false } = {}) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    rowSpan, columnSpan,
    verticalAlign: VerticalAlign.CENTER,
    borders: cellBorders({ top, bottom }),
    margins: { top: 80, bottom: 80, left: 100, right: 100 },
    children: [
      new Paragraph({
        alignment: align,
        children: [new TextRun({ text, bold, italics, font: FONT, size: 20 })],
      }),
    ],
  });
}

const COLS = [2500, 1715, 1715, 1715, 1715];

// ---- Row 1: spanner headings (2030 / 2060) ----
function spannerRow() {
  return new TableRow({
    children: [
      cell("Province", { width: COLS[0], top: THICK, rowSpan: 2, align: AlignmentType.LEFT }),
      cell("2030", { width: COLS[1] + COLS[2], top: THICK, bold: true, columnSpan: 2 }),
      cell("2060", { width: COLS[3] + COLS[4], top: THICK, bold: true, columnSpan: 2 }),
    ],
  });
}

// ---- Row 2: sub-headers ----
function subHeaderRow() {
  const labels = ["Cov(p, h)", "Provincial\nbias (%)", "Cov(p, h)", "Provincial\nbias (%)"];
  return new TableRow({
    children: labels.map((l, i) => {
      const lines = l.split("\n");
      return new TableCell({
        width: { size: COLS[i + 1], type: WidthType.DXA },
        verticalAlign: VerticalAlign.CENTER,
        borders: cellBorders({ bottom: THIN }),
        margins: { top: 40, bottom: 80, left: 100, right: 100 },
        children: lines.map(
          (t) => new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [new TextRun({ text: t, bold: true, font: FONT, size: 20 })],
          })
        ),
      });
    }),
  });
}

function dataRow(province, cov30, bias30, cov60, bias60, { bottomRow = false, italics = false } = {}) {
  const b = bottomRow ? THICK : undefined;
  return new TableRow({
    children: [
      cell(province, { align: AlignmentType.LEFT, width: COLS[0], bottom: b, italics }),
      cell(cov30, { align: AlignmentType.RIGHT, width: COLS[1], bottom: b, italics }),
      cell(bias30, { align: AlignmentType.RIGHT, width: COLS[2], bottom: b, italics }),
      cell(cov60, { align: AlignmentType.RIGHT, width: COLS[3], bottom: b, italics }),
      cell(bias60, { align: AlignmentType.RIGHT, width: COLS[4], bottom: b, italics }),
    ],
  });
}

const rows = [
  spannerRow(),
  subHeaderRow(),
  dataRow("Gangwon-do", "92.0", "−54.5%", "99.6", "−45.1%"),
  dataRow("Gyeonggi-do", "885.1", "−19.3%", "776.2", "−13.1%"),
  dataRow("Gyeongsangnam-do", "22.0", "+3.2%", "104.8", "−3.1%"),
  dataRow("Gyeongsangbuk-do", "112.6", "−35.0%", "155.2", "−29.9%"),
  dataRow("Jeollanam-do", "64.8", "−9.3%", "87.8", "+0.4%"),
  dataRow("Jeollabuk-do", "306.7", "−39.9%", "369.1", "−30.0%"),
  dataRow("Jeju-do", "56.1", "−22.6%", "181.6", "−18.0%"),
  dataRow("Chungcheongnam-do", "144.7", "−17.0%", "141.0", "−8.2%"),
  dataRow("Chungcheongbuk-do", "189.0", "−34.9%", "253.3", "−29.8%", { bottomRow: true }),
];

const table = new Table({ width: { size: TABLE_W, type: WidthType.DXA }, columnWidths: COLS, rows });

const title = new Paragraph({
  spacing: { after: 120 },
  children: [
    new TextRun({
      text: "Table Y. Grid-cell population–heat covariance and provincial-scale relative bias, by province (2030, 2060).",
      bold: true, font: FONT, size: 22,
    }),
  ],
});

const note = new Paragraph({
  spacing: { before: 100 },
  children: [
    new TextRun({
      text: "Note: Cov(p, h) is the covariance between population and extreme-heat-day count across 1 km grid cells within each province (person·days; higher values indicate that densely populated areas and severely heat-exposed areas spatially overlap more within that province). Provincial bias (%) is the relative bias of the provincial-scale (Method A) exposure estimate versus the 1 km grid (ground truth), reproduced from Fig. 2. Provinces are the 9 non-metropolitan do; metropolitan cities are excluded, consistent with Fig. 2's scope. Gyeongsangnam-do has the smallest Cov(p, h) of the 9 provinces in both years, consistent with its near-zero, sign-unstable bias.",
      italics: true, font: FONT, size: 18,
    }),
  ],
});

const doc = new Document({
  sections: [
    {
      properties: {
        page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } },
      },
      children: [title, table, note],
    },
  ],
});

Packer.toBuffer(doc).then((buf) => {
  require("fs").writeFileSync("Table_covariance.docx", buf);
  console.log("done");
});
