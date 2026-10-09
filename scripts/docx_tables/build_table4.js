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

// runs: array of {text, italics}
function cellRuns(runs, { align = AlignmentType.CENTER, width, bold = false, top, bottom } = {}) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    verticalAlign: VerticalAlign.CENTER,
    borders: cellBorders({ top, bottom }),
    margins: { top: 80, bottom: 80, left: 100, right: 100 },
    children: [
      new Paragraph({
        alignment: align,
        children: runs.map((r) => new TextRun({ text: r.text, italics: !!r.italics, bold, font: FONT, size: 20 })),
      }),
    ],
  });
}

function cell(text, opts = {}) {
  return cellRuns([{ text }], opts);
}

// value + optional italic share in parentheses, e.g. "563.67" + " (193.0%)"
function valCell(value, share, opts = {}) {
  const runs = [{ text: value }];
  if (share !== undefined) runs.push({ text: ` (${share})`, italics: true });
  return cellRuns(runs, opts);
}

const COLS = [1900, 1700, 1700, 1700, 1200, 1160];

function headerRow() {
  const labels = ["Metric", "1 km grid", "Municipal", "Provincial", "Municipal\nbias (%)", "Provincial\nbias (%)"];
  return new TableRow({
    children: labels.map((l, i) => {
      const lines = l.split("\n");
      return new TableCell({
        width: { size: COLS[i], type: WidthType.DXA },
        verticalAlign: VerticalAlign.CENTER,
        borders: cellBorders({ top: THICK, bottom: THIN }),
        margins: { top: 80, bottom: 80, left: 100, right: 100 },
        children: lines.map(
          (t) => new Paragraph({
            alignment: i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER,
            children: [new TextRun({ text: t, bold: true, font: FONT, size: 20 })],
          })
        ),
      });
    }),
  });
}

function plainRow(metric, grid, muni, prov, mbias, pbias, { bottomRow = false } = {}) {
  return new TableRow({
    children: [
      cell(metric, { align: AlignmentType.LEFT, width: COLS[0], bottom: bottomRow ? THICK : undefined }),
      cell(grid, { width: COLS[1], bottom: bottomRow ? THICK : undefined }),
      cell(muni, { width: COLS[2], bottom: bottomRow ? THICK : undefined }),
      cell(prov, { width: COLS[3], bottom: bottomRow ? THICK : undefined }),
      cell(mbias, { width: COLS[4], bottom: bottomRow ? THICK : undefined }),
      cell(pbias, { width: COLS[5], bottom: bottomRow ? THICK : undefined }),
    ],
  });
}

function effectRow(metric, grid, gshare, muni, mshare, prov, pshare, mbias, pbias, { bottomRow = false } = {}) {
  return new TableRow({
    children: [
      cell(metric, { align: AlignmentType.LEFT, width: COLS[0], bottom: bottomRow ? THICK : undefined }),
      valCell(grid, gshare, { width: COLS[1], bottom: bottomRow ? THICK : undefined }),
      valCell(muni, mshare, { width: COLS[2], bottom: bottomRow ? THICK : undefined }),
      valCell(prov, pshare, { width: COLS[3], bottom: bottomRow ? THICK : undefined }),
      cell(mbias, { width: COLS[4], bottom: bottomRow ? THICK : undefined }),
      cell(pbias, { width: COLS[5], bottom: bottomRow ? THICK : undefined }),
    ],
  });
}

const rows = [
  headerRow(),
  plainRow("Exposure, 2030 (E₀)", "642.70", "508.00", "472.31", "−", "−"),
  plainRow("Exposure, 2060 (E₁)", "934.72", "763.59", "723.77", "−", "−"),
  plainRow("Total change (ΔE)", "292.02", "255.59", "251.46", "−12.5%", "−13.9%"),
  effectRow("  Climate effect", "563.67", "193.0%", "470.75", "184.2%", "455.40", "181.1%", "−16.5%", "−19.2%"),
  effectRow("  Population effect", "−145.19", "−49.7%", "−111.67", "−43.7%", "−103.52", "−41.2%", "−23.1%", "−28.7%"),
  effectRow("  Interaction effect", "−126.47", "−43.3%", "−103.49", "−40.5%", "−100.41", "−39.9%", "−18.2%", "−20.6%", { bottomRow: true }),
];

const table = new Table({ width: { size: TABLE_W, type: WidthType.DXA }, columnWidths: COLS, rows });

const title = new Paragraph({
  spacing: { after: 120 },
  children: [
    new TextRun({
      text: "Table X. Scale-dependent decomposition of national exposure change (2030–2060) into climate, population, and interaction effects.",
      bold: true, font: FONT, size: 22,
    }),
  ],
});

const note = new Paragraph({
  spacing: { before: 100 },
  children: [
    new TextRun({
      text: "Note: Values are in millions of person-days. Italicized figures in parentheses show each effect's share (%) of that scale's total change (ΔE); these three shares sum to 100% within each column. The two rightmost columns show the percent bias of the municipal/provincial estimate relative to the 1 km grid (ground-truth) value, (aggregate − grid) / grid × 100. n = 106,553 grid cells, 161 municipalities, 17 provinces.",
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
  require("fs").writeFileSync("Table_decomposition_v4.docx", buf);
  console.log("done");
});
