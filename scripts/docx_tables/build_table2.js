const {
  Document, Packer, Paragraph, Table, TableRow, TableCell, TextRun,
  WidthType, AlignmentType, ShadingType, VerticalAlign,
} = require("docx");

const FONT = "Arial";
const TABLE_W = 9360;
const COLS = [1850, 1800, 1800, 1800, 1060, 1050];

function cell(text, { align = AlignmentType.CENTER, width } = {}) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    verticalAlign: VerticalAlign.CENTER,
    margins: { top: 80, bottom: 80, left: 100, right: 100 },
    children: [
      new Paragraph({
        alignment: align,
        children: [new TextRun({ text, font: FONT, size: 20 })],
      }),
    ],
  });
}

function headerRow() {
  const labels = [
    "Metric",
    "1 km grid\n(n = 106,553)",
    "Municipal\n(n = 161)",
    "Provincial\n(n = 17)",
    "Muni.\nbias (%)",
    "Prov.\nbias (%)",
  ];
  return new TableRow({
    tableHeader: true,
    children: labels.map((l, i) => {
      const lines = l.split("\n");
      return new TableCell({
        width: { size: COLS[i], type: WidthType.DXA },
        verticalAlign: VerticalAlign.CENTER,
        shading: { type: ShadingType.CLEAR, fill: "D9D9D9" },
        margins: { top: 80, bottom: 80, left: 100, right: 100 },
        children: lines.map(
          (t) =>
            new Paragraph({
              alignment: AlignmentType.CENTER,
              children: [new TextRun({ text: t, bold: true, font: FONT, size: 20 })],
            })
        ),
      });
    }),
  });
}

function dataRow(metric, grid, muni, prov, mbias, pbias) {
  return new TableRow({
    children: [
      cell(metric, { align: AlignmentType.LEFT, width: COLS[0] }),
      cell(grid, { width: COLS[1] }),
      cell(muni, { width: COLS[2] }),
      cell(prov, { width: COLS[3] }),
      cell(mbias, { width: COLS[4] }),
      cell(pbias, { width: COLS[5] }),
    ],
  });
}

const rows = [
  headerRow(),
  dataRow("Exposure, 2030 (E₀)", "642.70", "508.00", "472.31", "−", "−"),
  dataRow("Exposure, 2060 (E₁)", "934.72", "763.59", "723.77", "−", "−"),
  dataRow("Total change (ΔE)", "292.02", "255.59", "251.46", "−12.5%", "−13.9%"),
  dataRow("  Climate effect", "563.67 (193.0%)", "470.75 (184.2%)", "455.40 (181.1%)", "−16.5%", "−19.2%"),
  dataRow("  Population effect", "−145.19 (−49.7%)", "−111.67 (−43.7%)", "−103.52 (−41.2%)", "−23.1%", "−28.7%"),
  dataRow("  Interaction effect", "−126.47 (−43.3%)", "−103.49 (−40.5%)", "−100.41 (−39.9%)", "−18.2%", "−20.6%"),
];

const table = new Table({
  width: { size: TABLE_W, type: WidthType.DXA },
  columnWidths: COLS,
  rows,
});

const title = new Paragraph({
  spacing: { after: 120 },
  children: [
    new TextRun({
      text: "Table X. Scale-dependent decomposition of national exposure change (2030–2060) into climate, population, and interaction effects.",
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
      children: [title, table],
    },
  ],
});

Packer.toBuffer(doc).then((buf) => {
  require("fs").writeFileSync("Table_decomposition_v2.docx", buf);
  console.log("done");
});
