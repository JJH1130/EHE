const {
  Document, Packer, Paragraph, Table, TableRow, TableCell, TextRun,
  WidthType, AlignmentType, ShadingType, BorderStyle, HeadingLevel,
  VerticalAlign,
} = require("docx");

const FONT = "Arial";
const TABLE_W = 9360; // DXA, ~6.5in content width on US Letter
// columns: Metric(2400) | Grid(1520) | Municipal(1520) | Provincial(1520) | Muni bias(1200) | Prov bias(1200)
const COLS = [2400, 1520, 1520, 1520, 1200, 1200];

function cell(text, { bold = false, align = AlignmentType.CENTER, shade = null, width, italics = false } = {}) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    verticalAlign: VerticalAlign.CENTER,
    shading: shade ? { type: ShadingType.CLEAR, fill: shade } : undefined,
    margins: { top: 80, bottom: 80, left: 100, right: 100 },
    children: [
      new Paragraph({
        alignment: align,
        children: [new TextRun({ text, bold, italics, font: FONT, size: 20 })],
      }),
    ],
  });
}

function headerRow() {
  const labels = ["Metric", "1 km grid\n(n = 106,553)", "Municipal\n(n = 161)", "Provincial\n(n = 17)", "Municipal\nbias (%)", "Provincial\nbias (%)"];
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

function dataRow(metric, grid, muni, prov, mbias, pbias, { shade = null, bold = false, italics = false } = {}) {
  return new TableRow({
    children: [
      cell(metric, { align: AlignmentType.LEFT, width: COLS[0], shade, bold, italics }),
      cell(grid, { width: COLS[1], shade, bold, italics }),
      cell(muni, { width: COLS[2], shade, bold, italics }),
      cell(prov, { width: COLS[3], shade, bold, italics }),
      cell(mbias, { width: COLS[4], shade, bold, italics }),
      cell(pbias, { width: COLS[5], shade, bold, italics }),
    ],
  });
}

const rows = [
  headerRow(),
  dataRow("Exposure, 2030 (E₀)", "642.70", "508.00", "472.31", "−", "−"),
  dataRow("Exposure, 2060 (E₁)", "934.72", "763.59", "723.77", "−", "−"),
  dataRow("Total change (ΔE = E₁ − E₀)", "292.02", "255.59", "251.46", "−12.5%", "−13.9%", { bold: true, shade: "F2F2F2" }),
  dataRow("  Climate effect", "563.67", "470.75", "455.40", "−16.5%", "−19.2%"),
  dataRow("  Population effect", "−145.19", "−111.67", "−103.52", "−23.1%", "−28.7%"),
  dataRow("  Interaction effect", "−126.47", "−103.49", "−100.41", "−18.2%", "−20.6%"),
  dataRow("  Check (sum of 3 effects)", "292.02", "255.59", "251.46", "", "", { italics: true }),
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

const note = new Paragraph({
  spacing: { before: 160 },
  children: [
    new TextRun({
      text: "Note: Values are in millions of person-days, except the two rightmost columns. Exposure (E) is decomposed as ΔE = P₀·ΔH + H₀·ΔP + ΔP·ΔH, where P and H are population and number of extreme-heat days, and subscripts 0/1 denote 2030/2060. “Bias (%)” is the relative difference of the municipal or provincial estimate from the 1 km grid value, (aggregate − grid) / grid × 100. Municipal (n = 161) and provincial (n = 17) totals use all administrative units nationwide, including metropolitan cities; this differs from Fig. 2, which compares the subset of 9 non-metropolitan provinces (do) only.",
      italics: true,
      font: FONT,
      size: 18,
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
  require("fs").writeFileSync("Table_decomposition.docx", buf);
  console.log("done");
});
