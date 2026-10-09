const {
  Document, Packer, Paragraph, Table, TableRow, TableCell, TextRun,
  WidthType, AlignmentType, VerticalAlign, BorderStyle,
} = require("docx");

const FONT = "Arial";
const TABLE_W = 9360;
const NONE = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const THIN = { style: BorderStyle.SINGLE, size: 4, color: "000000" };   // ~0.5pt
const THICK = { style: BorderStyle.SINGLE, size: 8, color: "000000" }; // ~1pt

// borders: no vertical lines anywhere; horizontal lines only at
// table top, below header row, and table bottom (classic "open" journal style)
function cellBorders({ top = NONE, bottom = NONE } = {}) {
  return { top, bottom, left: NONE, right: NONE };
}

function cell(text, { align = AlignmentType.CENTER, width, bold = false, top, bottom } = {}) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    verticalAlign: VerticalAlign.CENTER,
    borders: cellBorders({ top, bottom }),
    margins: { top: 80, bottom: 80, left: 100, right: 100 },
    children: [
      new Paragraph({
        alignment: align,
        children: [new TextRun({ text, bold, font: FONT, size: 20 })],
      }),
    ],
  });
}

// ---------------------------------------------------------------------
// Table 2a: absolute magnitude (M person-days) + bias vs. grid (%)
// ---------------------------------------------------------------------
const COLS_A = [1900, 1700, 1700, 1700, 1200, 1160];

function rowA(cells, { topRow = false, headerSep = false, bottomRow = false, bold = false } = {}) {
  return new TableRow({
    children: cells.map((text, i) =>
      cell(text, {
        align: i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER,
        width: COLS_A[i],
        bold,
        top: topRow ? THICK : undefined,
        bottom: bottomRow ? THICK : headerSep ? THIN : undefined,
      })
    ),
  });
}

const tableA = new Table({
  width: { size: TABLE_W, type: WidthType.DXA },
  columnWidths: COLS_A,
  rows: [
    rowA(["Metric", "1 km grid", "Municipal", "Provincial", "Municipal\nbias (%)", "Provincial\nbias (%)"].map((t)=>t), { topRow: true, bold: true })
      // replace with multi-line header built manually below
  ],
});

// Build header row manually to allow two-line labels
function headerRowA() {
  const labels = ["Metric", "1 km grid", "Municipal", "Provincial", "Municipal bias (%)", "Provincial bias (%)"];
  return new TableRow({
    children: labels.map((t, i) =>
      cell(t, { align: i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER, width: COLS_A[i], bold: true, top: THICK, bottom: THIN })
    ),
  });
}

const tableA_rows = [
  headerRowA(),
  rowA(["Exposure, 2030 (E₀)", "642.70", "508.00", "472.31", "−", "−"]),
  rowA(["Exposure, 2060 (E₁)", "934.72", "763.59", "723.77", "−", "−"]),
  rowA(["Total change (ΔE)", "292.02", "255.59", "251.46", "−12.5%", "−13.9%"]),
  rowA(["  Climate effect", "563.67", "470.75", "455.40", "−16.5%", "−19.2%"]),
  rowA(["  Population effect", "−145.19", "−111.67", "−103.52", "−23.1%", "−28.7%"]),
  rowA(["  Interaction effect", "−126.47", "−103.49", "−100.41", "−18.2%", "−20.6%"], { bottomRow: true }),
];

const tableA_final = new Table({ width: { size: TABLE_W, type: WidthType.DXA }, columnWidths: COLS_A, rows: tableA_rows });

// ---------------------------------------------------------------------
// Table 2b: share of total exposure change (%) attributable to each
// effect, by spatial scale
// ---------------------------------------------------------------------
const COLS_B = [2400, 2320, 2320, 2320];

function rowB(cells, { headerSep = false, bottomRow = false, bold = false, topRow = false } = {}) {
  return new TableRow({
    children: cells.map((text, i) =>
      cell(text, {
        align: i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER,
        width: COLS_B[i],
        bold,
        top: topRow ? THICK : undefined,
        bottom: bottomRow ? THICK : headerSep ? THIN : undefined,
      })
    ),
  });
}

const tableB_rows = [
  rowB(["Effect", "1 km grid", "Municipal", "Provincial"], { topRow: true, headerSep: true, bold: true }),
  rowB(["Climate effect", "193.0%", "184.2%", "181.1%"]),
  rowB(["Population effect", "−49.7%", "−43.7%", "−41.2%"]),
  rowB(["Interaction effect", "−43.3%", "−40.5%", "−39.9%"]),
  rowB(["Total change", "100.0%", "100.0%", "100.0%"], { bottomRow: true }),
];

const tableB_final = new Table({ width: { size: TABLE_W, type: WidthType.DXA }, columnWidths: COLS_B, rows: tableB_rows });

// ---------------------------------------------------------------------
// Assemble
// ---------------------------------------------------------------------
const titleA = new Paragraph({
  spacing: { after: 120 },
  children: [
    new TextRun({
      text: "Table X. Scale-dependent decomposition of national exposure change (2030–2060) into climate, population, and interaction effects (million person-days).",
      bold: true,
      font: FONT,
      size: 22,
    }),
  ],
});

const noteA = new Paragraph({
  spacing: { before: 100, after: 400 },
  children: [
    new TextRun({
      text: "n = 106,553 grid cells; 161 municipalities; 17 provinces. Bias (%) = (aggregate − grid) / grid × 100.",
      italics: true,
      font: FONT,
      size: 18,
    }),
  ],
});

const titleB = new Paragraph({
  spacing: { after: 120 },
  children: [
    new TextRun({
      text: "Table Y. Relative contribution of each effect to total exposure change (% of ΔE), by spatial scale.",
      bold: true,
      font: FONT,
      size: 22,
    }),
  ],
});

const doc = new Document({
  sections: [
    {
      properties: {
        page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } },
      },
      children: [titleA, tableA_final, noteA, titleB, tableB_final],
    },
  ],
});

Packer.toBuffer(doc).then((buf) => {
  require("fs").writeFileSync("Table_decomposition_v3.docx", buf);
  console.log("done");
});
