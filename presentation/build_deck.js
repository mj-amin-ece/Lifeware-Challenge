// Builds NAMA_Neuron_Migration.pptx: the 5-minute talk of team NAMA, with speaker notes.
//
//   NODE_PATH=<folder with pptxgenjs, react, react-dom, react-icons, sharp> node build_deck.js
//
// The USI logo is read from usi_logo.png (or .jpg) next to this script; without it the slides show an empty slot.
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const React = require("react");
const { renderToStaticMarkup } = require("react-dom/server");
const sharp = require("sharp");
const { FaDatabase, FaLightbulb, FaSearch, FaCode, FaClock, FaChartLine, FaBug, FaProjectDiagram, FaCalendarAlt, FaTags, FaSlidersH, FaCheckDouble, FaBalanceScale } = require("react-icons/fa");
const { applyTheme } = require(process.env.APPLY_THEME);

const THEME = {
  name: "NAMA Neuron",
  headFontFace: "Times New Roman",
  bodyFontFace: "Times New Roman",
  colors: {
    dk1: "16212E", lt1: "FFFFFF", dk2: "2E4057", lt2: "EEF2F6",
    accent1: "D52B1E", accent2: "2E4057", accent3: "1F8A70", accent4: "6B7A8F", accent5: "F4A259", accent6: "A8B5C6",
    hlink: "D52B1E", folHlink: "6B7A8F",
  },
};
const OUT = path.join(__dirname, "NAMA_Neuron_Migration.pptx");
const ERA_CSV = path.join(__dirname, "..", "Plots", "errors_by_era.csv");
const LOGO = ["usi_logo.png", "usi_logo.jpg", "usi_logo.jpeg"].map((f) => path.join(__dirname, f)).find((f) => fs.existsSync(f));
const MEMBERS = "Mohammad Javad Amin  ·  Nava Biglar  ·  Malihe Ghasemian  ·  Emad Aghajani";

async function icon(Icon, color) {
  const svg = renderToStaticMarkup(React.createElement(Icon, { color: "#" + color, size: 256 }));
  return "image/png;base64," + (await sharp(Buffer.from(svg)).png().toBuffer()).toString("base64");
}

// White card with the USI logo (logos are black on white, so they sit on their own card on dark slides)
function logoCard(slide, pres, C, x, y, w, h) {
  if (!LOGO) return;
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: C.background1 }, line: { color: C.background1 }, objectName: "Logo card" });
  const iw = w - 0.2, ih = iw * 900 / 1600;
  slide.addImage({ path: LOGO, x: x + 0.1, y: y + (h - ih) / 2, w: iw, h: ih, altText: "Università della Svizzera italiana logo", objectName: "USI logo" });
}

async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9"; // 10 x 5.625 in
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  pres.title = "The Neuron Migration";
  pres.author = "Team NAMA";
  const C = pres.SchemeColor;

  // Layouts --------------------------------------------------------------------------------------------------------
  pres.defineSlideMaster({
    title: "Title dark",
    background: { color: C.text1 },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 2.05, w: 8.8, h: 0.85, fontSize: 40, bold: true, color: C.background1, fontFace: THEME.headFontFace, align: "left", valign: "bottom", margin: 0 }, text: "" } },
      { placeholder: { options: { name: "body", type: "body", x: 0.6, y: 2.95, w: 8.8, h: 0.7, fontSize: 18, color: C.accent6, align: "left", valign: "top", margin: 0 }, text: "" } },
    ],
  });
  const footer = [
    { text: { text: "Team NAMA  ·  The Neuron Migration", options: { x: 0.5, y: 5.2, w: 5, h: 0.3, fontSize: 10, color: C.accent4, margin: 0 } } },
  ];
  if (LOGO) footer.push({ image: { path: LOGO, x: 8.62, y: 5.05, w: 0.9, h: 0.506, altText: "USI logo" } });
  pres.defineSlideMaster({
    title: "Content",
    background: { color: C.background1 },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.3, w: 9.0, h: 0.7, fontSize: 30, bold: true, color: C.text1, fontFace: THEME.headFontFace, valign: "top", margin: 0 }, text: "" } },
      ...footer,
    ],
    slideNumber: { x: 8.1, y: 5.2, w: 0.4, h: 0.3, fontSize: 10, color: C.accent4, align: "right" },
  });

  // 1 Title --------------------------------------------------------------------------------------------------------
  pres.addSection({ title: "Opening" });
  let s = pres.addSlide({ masterName: "Title dark", sectionTitle: "Opening" });
  logoCard(s, pres, C, 0.6, 0.45, 2.6, 1.55);
  s.addText("Lifeware Challenge  ·  Neural Wave AI Hackathon", { x: 4.4, y: 0.6, w: 5.0, h: 0.35, fontSize: 12, color: C.accent6, align: "right", margin: 0, isTextBox: true, objectName: "Event" });
  s.addText("The Neuron Migration", { placeholder: "title" });
  s.addText("Reverse-engineering 30 years of insurance logic into code an auditor can check", { placeholder: "body" });
  s.addText("TEAM NAMA", { x: 0.6, y: 4.1, w: 4, h: 0.35, fontSize: 14, bold: true, color: C.accent1, charSpacing: 2, margin: 0, isTextBox: true, objectName: "Team name" });
  s.addText(MEMBERS, { x: 0.6, y: 4.45, w: 8.8, h: 0.4, fontSize: 16, color: C.background1, margin: 0, isTextBox: true, objectName: "Members" });
  s.addNotes(
    "Hello, we are team NAMA from USI: Mohammad Javad Amin, Nava Biglar, Malihe Ghasemian and Emad Aghajani. " +
    "Our challenge was the Neuron migration: rebuilding thirty years of insurance logic as code that an auditor can check. We show how we did it, and why the same method also worked on a task without any answers."
  );

  // 2 Challenge ----------------------------------------------------------------------------------------------------
  pres.addSection({ title: "Challenge" });
  s = pres.addSlide({ masterName: "Content", sectionTitle: "Challenge" });
  s.addText("Match Neuron to the cent, without its code", { placeholder: "title" });
  s.addText([
    { text: "NeuralWave Life moves its unit-linked policies from the legacy system Neuron to Lifeware", options: { bullet: true, breakLine: true } },
    { text: "Neuron grew from COBOL to Java since 1994; the developers are gone, the documentation is incomplete", options: { bullet: true, breakLine: true } },
    { text: "Only the data is left, and Neuron's results for part of the policies", options: { bullet: true } },
  ], { x: 0.5, y: 1.3, w: 4.3, h: 2.6, fontSize: 16, color: C.text1, paraSpaceAfter: 10, valign: "top", margin: 0, isTextBox: true, objectName: "Story" });
  s.addText("A value counts only if it is exact: to the cent and to the day.", { x: 0.5, y: 4.25, w: 4.3, h: 0.6, fontSize: 15, italic: true, color: C.accent1, margin: 0, isTextBox: true, objectName: "Scoring rule" });
  const stats = [["5,000", "policies since 1994"], ["6.8 M", "unit bookings"], ["27", "legacy tables"], ["0", "lines of source code"]];
  stats.forEach(([value, label], i) => {
    const x = 5.2 + (i % 2) * 2.2, y = 1.3 + Math.floor(i / 2) * 1.8;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 2.05, h: 1.6, rectRadius: 0.08, fill: { color: C.background2 }, line: { color: C.background2 }, objectName: `Stat card ${i + 1}` });
    s.addText(value, { x: x + 0.15, y: y + 0.2, w: 1.75, h: 0.75, fontSize: 36, bold: true, fontFace: THEME.headFontFace, color: i === 3 ? C.accent1 : C.text1, margin: 0, isTextBox: true, objectName: `Stat value ${i + 1}` });
    s.addText(label, { x: x + 0.15, y: y + 0.95, w: 1.75, h: 0.45, fontSize: 13, color: C.text2, margin: 0, isTextBox: true, objectName: `Stat label ${i + 1}` });
  });
  s.addNotes(
    "NeuralWave Life wants to move its unit-linked policies from its legacy system Neuron to Lifeware. " +
    "Neuron has run since 1994, first in COBOL and later in Java. The developers are gone and there is no source code. " +
    "What we have is the export: 27 tables, 5,000 policies, almost seven million fund bookings, and the values Neuron calculated for part of the policies. " +
    "And the bar is high: a value only counts if it matches to the cent and to the day."
  );

  // 3 Approach -----------------------------------------------------------------------------------------------------
  pres.addSection({ title: "Approach" });
  s = pres.addSlide({ masterName: "Content", sectionTitle: "Approach" });
  s.addText("AI is the detective, code is the answer", { placeholder: "title" });
  const steps = [
    [FaDatabase, "Decode", "One loader for all 27 tables, driven by the data dictionary NRDICT"],
    [FaLightbulb, "Guess", "The simplest rule the task text suggests"],
    [FaSearch, "Explain the misses", "Decision-tree rule finder, convention search, booking-by-booking checks"],
    [FaCode, "Encode", "Plain Python with exact decimals, one small module per task"],
  ];
  for (const [i, [Icon, head, text]] of steps.entries()) {
    const x = 0.5 + i * 2.3;
    s.addShape(pres.shapes.OVAL, { x: x + 0.65, y: 1.3, w: 0.8, h: 0.8, fill: { color: i === 2 ? C.accent1 : C.text1 }, line: { color: i === 2 ? C.accent1 : C.text1 }, objectName: `Step circle ${i + 1}` });
    s.addImage({ data: await icon(Icon, "FFFFFF"), x: x + 0.85, y: 1.5, w: 0.4, h: 0.4, altText: head, objectName: `Step icon ${i + 1}` });
    if (i < 3) s.addShape(pres.shapes.CHEVRON, { x: x + 1.95, y: 1.55, w: 0.25, h: 0.3, fill: { color: C.accent6 }, line: { color: C.accent6 }, objectName: `Arrow ${i + 1}` });
    s.addText(`${i + 1}  ${head}`, { x, y: 2.25, w: 2.1, h: 0.4, fontSize: 16, bold: true, color: C.text1, align: "center", margin: 0, isTextBox: true, objectName: `Step title ${i + 1}` });
    s.addText(text, { x, y: 2.7, w: 2.1, h: 1.1, fontSize: 14, color: C.text2, align: "center", valign: "top", margin: 0, isTextBox: true, objectName: `Step text ${i + 1}` });
  }
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.5, y: 4.05, w: 9.0, h: 0.8, rectRadius: 0.08, fill: { color: C.background2 }, line: { color: C.background2 }, objectName: "Principle card" });
  s.addText([
    { text: "Machine learning shows where a rule breaks. ", options: { bold: true } },
    { text: "The submission contains no model: every cent can be explained to an auditor." },
  ], { x: 0.75, y: 4.05, w: 8.5, h: 0.8, fontSize: 15, color: C.text1, valign: "middle", margin: 0, isTextBox: true, objectName: "Principle" });
  s.addNotes(
    "So we used AI as the detective, not as the calculator. One loader decodes all 27 tables from the old data dictionary. " +
    "For each task we wrote the simplest rule and compared it with Neuron's numbers. " +
    "Where it failed, machine learning told us why: a shallow decision tree on the wrong rows, a search over rounding and date conventions, " +
    "and for the fund accounting a check of every single booking. " +
    "Every finding became plain Python with exact decimals, so every cent can be explained."
  );

  // 4 Toolkit ------------------------------------------------------------------------------------------------------
  s = pres.addSlide({ masterName: "Content", sectionTitle: "Approach" });
  s.addText("One loop, six generic tools", { placeholder: "title" });
  const toolkit = [
    [FaProjectDiagram, "Rule finder", "Where is a rule wrong? \u2192 drifting due dates before 2007"],
    [FaChartLine, "Change points", "When did the system change? \u2192 2007-08-11"],
    [FaSearch, "Residuals", "What do the differences say? \u2192 31/360, cut-off cents"],
    [FaSlidersH, "Convention search", "Which convention is it? \u2192 Actual/360, charge order"],
    [FaTags, "Weak labels", "No targets? Learn from the legacy bookings \u2192 t7"],
    [FaCalendarAlt, "Learned calendar", "Business days from the price days \u2192 Ticino holidays"],
  ];
  for (const [i, [Icon, name, text]] of toolkit.entries()) {
    const x = 0.5 + (i % 3) * 3.05, y = 1.2 + Math.floor(i / 3) * 1.7;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 2.9, h: 1.55, rectRadius: 0.08, fill: { color: C.background2 }, line: { color: C.background2 }, objectName: `Toolkit card ${i + 1}` });
    s.addShape(pres.shapes.OVAL, { x: x + 0.2, y: y + 0.2, w: 0.5, h: 0.5, fill: { color: i === 4 ? C.accent1 : C.text1 }, line: { color: i === 4 ? C.accent1 : C.text1 }, objectName: `Toolkit circle ${i + 1}` });
    s.addImage({ data: await icon(Icon, "FFFFFF"), x: x + 0.32, y: y + 0.32, w: 0.26, h: 0.26, altText: name, objectName: `Toolkit icon ${i + 1}` });
    s.addText(name, { x: x + 0.85, y: y + 0.22, w: 1.95, h: 0.45, fontSize: 16, bold: true, color: C.text1, valign: "middle", margin: 0, isTextBox: true, objectName: `Toolkit name ${i + 1}` });
    s.addText(text, { x: x + 0.2, y: y + 0.8, w: 2.55, h: 0.65, fontSize: 13, color: C.text2, valign: "top", margin: 0, isTextBox: true, objectName: `Toolkit text ${i + 1}` });
  }
  s.addText("None of them knows anything about insurance: notebook 06 shows each one rediscovering one of our rules.", { x: 0.5, y: 4.67, w: 9.0, h: 0.3, fontSize: 12, italic: true, color: C.text2, margin: 0, isTextBox: true, objectName: "Toolkit caption" });
  s.addNotes(
    "What makes this a method and not a one-off is the toolkit. Each tool answers a question that every migration has: " +
    "where is the rule wrong, on which day did the system change, what do the differences say, which convention is it, " +
    "and how do we learn when there are no targets. None of them knows anything about insurance. " +
    "In notebook six each tool rediscovers one of our rules on its own, for example the conversion date in August 2007."
  );

  // 5 Findings -----------------------------------------------------------------------------------------------------
  pres.addSection({ title: "Findings" });
  s = pres.addSlide({ masterName: "Content", sectionTitle: "Findings" });
  s.addText("Neuron is really two systems", { placeholder: "title" });
  const head = { bold: true, color: C.background1, fill: { color: C.text1 }, fontSize: 14 };
  const cell = (text, opts = {}) => ({ text, options: { fontSize: 14, color: C.text1, fill: { color: C.background1 }, ...opts } });
  const rows = [
    [{ text: "", options: head }, { text: "COBOL, until 2007", options: head }, { text: "Neuron NG, Java", options: head }],
    [cell("Rounding", { bold: true }), cell("truncate"), cell("half up")],
    [cell("Insured age", { bold: true }), cell("days since birth ÷ 365"), cell("nearest birthday")],
    [cell("Management charge", { bold: true }), cell("rate × days ÷ 360"), cell("rate ÷ 12")],
    [cell("Due dates", { bold: true }), cell("drift 31 → 30 → 28"), cell("anchored, no drift")],
  ];
  s.addTable(rows, { x: 0.5, y: 1.3, w: 5.7, colW: [1.7, 2.0, 2.0], rowH: 0.62, border: { type: "solid", pt: 0.75, color: THEME.colors.lt2 }, valign: "middle", objectName: "COBOL vs NG" });
  s.addText("Also hidden in the data", { x: 6.55, y: 1.3, w: 2.95, h: 0.35, fontSize: 16, bold: true, color: C.text1, margin: 0, isTextBox: true, objectName: "Also title" });
  const extras = [
    [FaClock, "The 01:30 charge run sees only units traded before the day"],
    [FaChartLine, "Each fund buys on its own first day with a price"],
    [FaBug, "Lowercase currency codes, impossible birth dates"],
  ];
  for (const [i, [Icon, text]] of extras.entries()) {
    const y = 1.8 + i * 1.0;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 6.55, y, w: 2.95, h: 0.85, rectRadius: 0.08, fill: { color: C.background2 }, line: { color: C.background2 }, objectName: `Extra card ${i + 1}` });
    s.addShape(pres.shapes.OVAL, { x: 6.7, y: y + 0.2, w: 0.45, h: 0.45, fill: { color: C.accent1 }, line: { color: C.accent1 }, objectName: `Extra circle ${i + 1}` });
    s.addImage({ data: await icon(Icon, "FFFFFF"), x: 6.8, y: y + 0.3, w: 0.25, h: 0.25, altText: "", objectName: `Extra icon ${i + 1}` });
    s.addText(text, { x: 7.3, y, w: 2.1, h: 0.85, fontSize: 13, color: C.text1, valign: "middle", margin: 0, isTextBox: true, objectName: `Extra text ${i + 1}` });
  }
  s.addNotes(
    "Our biggest discovery: Neuron is really two systems. Until the conversion in August 2007, COBOL truncated every amount, " +
    "computed the age as days since birth divided by 365, charged the management fee by the day, " +
    "and let due dates drift from the 31st to the 28th. Neuron NG rounds half up, uses the nearest birthday and charges a twelfth of the yearly rate. " +
    "We also found operational details: the charge run at 1:30 in the morning only sees units traded before that day, " +
    "and each fund buys on its own first price day."
  );

  // 6 Era evidence -------------------------------------------------------------------------------------------------
  s = pres.addSlide({ masterName: "Content", sectionTitle: "Findings" });
  s.addText("Ignore the two systems and the numbers break", { placeholder: "title" });
  const era = fs.readFileSync(ERA_CSV, "utf8").trim().split("\n").slice(1).map((line) => line.split(","))
    .filter((row) => row[1] !== "");
  const years = era.map((row) => row[0]);
  s.addChart([
    { type: pres.charts.AREA, data: [{ name: "COBOL era", labels: years, values: years.map((year) => (+year <= 2007 ? 100 : 0)) }],
      options: { chartColors: ["E1E6EC"] } },
    { type: pres.charts.LINE, data: [
        { name: "t4 statements, NG rules only", labels: years, values: era.map((row) => +row[1]) },
        { name: "t2 offers, NG rules only", labels: years, values: era.map((row) => +row[2]) },
        { name: "Our rules", labels: years, values: era.map((row) => +row[3]) },
      ], options: { chartColors: [THEME.colors.accent1, THEME.colors.accent5, THEME.colors.accent3], lineSize: 2.5, lineDataSymbol: "none" } },
  ], {
    x: 0.5, y: 1.2, w: 6.2, h: 3.75, objectName: "Errors per system era",
    valAxisMinVal: 0, valAxisMaxVal: 100, valAxisMajorUnit: 25, valAxisLabelFormatCode: '0"%"',
    valAxisLabelColor: THEME.colors.accent4, catAxisLabelColor: THEME.colors.accent4, valAxisLabelFontSize: 11, catAxisLabelFontSize: 11,
    valAxisLabelFontFace: "+mn-lt", catAxisLabelFontFace: "+mn-lt", catAxisLabelFrequency: 4,
    valGridLine: { color: "E5E9EF", size: 0.5 }, catGridLine: { style: "none" },
    showLegend: true, legendPos: "b", legendFontSize: 11, legendFontFace: "+mn-lt", legendColor: THEME.colors.dk2,
    showValAxisTitle: true, valAxisTitle: "Wrong values per year", valAxisTitleFontSize: 11, valAxisTitleColor: THEME.colors.accent4,
    valAxisTitleFontFace: "+mn-lt",
  });
  const evidence = [
    ["100 %", "of the offers of the COBOL era are wrong with the Neuron NG rules alone", C.accent1],
    ["17 %", "of the 2025 statements are still wrong: old errors live on in the balances", C.accent1],
    ["0 %", "with our era rules, apart from the manual corrections", C.accent3],
  ];
  evidence.forEach(([value, label, color], i) => {
    const y = 1.25 + i * 1.25;
    s.addText(value, { x: 7.0, y, w: 2.5, h: 0.55, fontSize: 30, bold: true, fontFace: THEME.headFontFace, color, margin: 0, isTextBox: true, objectName: `Era value ${i + 1}` });
    s.addText(label, { x: 7.0, y: y + 0.55, w: 2.5, h: 0.6, fontSize: 13, color: C.text2, valign: "top", margin: 0, isTextBox: true, objectName: `Era label ${i + 1}` });
  });
  s.addNotes(
    "How do we know this matters? We ran our own code once more, but moved the conversion to 1900, so the Neuron NG rules apply to every year. " +
    "Then every offer of the COBOL era is wrong, and the statements stay wrong long after 2007, because the old errors live on in the fund balances: " +
    "still 17 percent in 2025. With our era rules both lines drop to zero."
  );

  // 7 Results ------------------------------------------------------------------------------------------------------
  pres.addSection({ title: "Results" });
  s = pres.addSlide({ masterName: "Content", sectionTitle: "Results" });
  s.addText("Every remaining miss is a manual correction", { placeholder: "title" });
  const tasks = [["t0", "Commission", "99.996 %"], ["t1", "Due dates", "100 %"], ["t2", "Maturity value", "99.735 %"], ["t3", "Surrender value", "99.740 %"], ["t4", "Annual statement", "99.939 %"]];
  tasks.forEach(([id, name, score], i) => {
    const x = 0.5 + i * 1.825;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.25, w: 1.7, h: 1.25, rectRadius: 0.08, fill: { color: C.background2 }, line: { color: C.background2 }, objectName: `Task card ${id}` });
    s.addText(`${id}  ${name}`, { x: x + 0.12, y: 1.35, w: 1.5, h: 0.35, fontSize: 12, color: C.text2, margin: 0, isTextBox: true, objectName: `Task name ${id}` });
    s.addText(score, { x: x + 0.12, y: 1.75, w: 1.5, h: 0.55, fontSize: 24, bold: true, fontFace: THEME.headFontFace, color: C.accent3, margin: 0, isTextBox: true, objectName: `Task score ${id}` });
  });
  const callouts = [
    ["5,024,847", "fund bookings recalculated from scratch: all exact except 3 changed by hand"],
    ["55", "hand-edited values found automatically (t5): all 38 listed ones and 17 new"],
  ];
  callouts.forEach(([value, label], i) => {
    const x = 0.5 + i * 4.6;
    s.addText(value, { x, y: 2.85, w: 4.4, h: 0.85, fontSize: 44, bold: true, fontFace: THEME.headFontFace, color: i === 1 ? C.accent1 : C.text1, margin: 0, isTextBox: true, objectName: `Callout value ${i + 1}` });
    s.addText(label, { x, y: 3.7, w: 4.2, h: 0.65, fontSize: 15, color: C.text2, valign: "top", margin: 0, isTextBox: true, objectName: `Callout label ${i + 1}` });
  });
  s.addText("Train set, official scoring  ·  t0\u2013t5 run in 45 seconds  ·  maintainability index 68", { x: 0.5, y: 4.6, w: 9.0, h: 0.3, fontSize: 11, color: C.accent4, margin: 0, isTextBox: true, objectName: "Results caption" });
  s.addNotes(
    "With these rules we reach between 99.7 and 100 percent on every task. " +
    "For surrender values and statements we recalculate the whole fund accounting ourselves, more than five million bookings, " +
    "and every one of them matches Neuron except three that were changed by hand. " +
    "In fact, every remaining difference is a manual correction, and our outlier detection for task five finds them automatically: " +
    "55 values, including all 38 from the official list and 17 that nobody had listed. Tasks zero to five run in about 45 seconds, with one small module per task."
  );

  // 8 t7: the method ------------------------------------------------------------------------------------------------
  pres.addSection({ title: "Surprise t7" });
  const PLOT = (name) => path.join(__dirname, "plots", name);
  s = pres.addSlide({ masterName: "Content", sectionTitle: "Surprise t7" });
  s.addText("Surprise t7: from guesses to exact rules", { placeholder: "title" });
  const steps7 = [
    [FaTags, "1  Weak labels", "Neuron's tax bookings say which tax it charged: the gates match 498 of 498 countries"],
    [FaChartLine, "2  Leaderboard splits", "Each half of the policies gets a different rule; the count says which one was right"],
    [FaSearch, "3  One rule per mismatch", "On the organisers' samples every wrong row got its own rule, checked on all 110 rows"],
    [FaBalanceScale, "4  The law decides", "Where no sample shows the case, the rule follows Swiss, Italian and German law"],
  ];
  for (const [i, [Icon, name, text]] of steps7.entries()) {
    const x = 0.5 + i * 2.3;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.2, w: 2.15, h: 3.0, rectRadius: 0.08, fill: { color: C.background2 }, line: { color: C.background2 }, objectName: `t7 step card ${i + 1}` });
    s.addShape(pres.shapes.OVAL, { x: x + 0.2, y: 1.4, w: 0.6, h: 0.6, fill: { color: C.accent1 }, line: { color: C.accent1 }, objectName: `t7 step circle ${i + 1}` });
    s.addImage({ data: await icon(Icon, "FFFFFF"), x: x + 0.35, y: 1.55, w: 0.3, h: 0.3, altText: name, objectName: `t7 step icon ${i + 1}` });
    s.addText(name, { x: x + 0.2, y: 2.15, w: 1.8, h: 0.6, fontSize: 15, bold: true, color: C.text1, valign: "top", margin: 0, isTextBox: true, objectName: `t7 step name ${i + 1}` });
    s.addText(text, { x: x + 0.2, y: 2.8, w: 1.8, h: 1.3, fontSize: 12, color: C.text2, valign: "top", margin: 0, isTextBox: true, objectName: `t7 step text ${i + 1}` });
  }
  s.addText("No targets at first, two examples, and a leaderboard of 40 payouts and 30 policy years.", { x: 0.5, y: 4.4, w: 9.0, h: 0.4, fontSize: 14, italic: true, color: C.accent1, margin: 0, isTextBox: true, objectName: "t7 setting" });
  s.addNotes(
    "Then came the surprise: a tax audit for three countries since 1994, with no target values at all. We found the rules in four steps. " +
    "First, weak labels: Neuron's own tax bookings have no amounts, but they say which tax it charged, so our gates match them exactly. " +
    "Second, the leaderboard as an instrument: we gave each half of the policies a different rule, so one upload tested two ideas. " +
    "Third, when the organisers published two samples, we traced every wrong row to its own rule and kept a rule only if it held on all 110 rows. " +
    "And fourth, where no sample shows a case, the rule follows the law."
  );

  // 9 t7: one mismatch, one rule -------------------------------------------------------------------------------------
  s = pres.addSlide({ masterName: "Content", sectionTitle: "Surprise t7" });
  s.addText("One mismatch, one rule", { placeholder: "title" });
  const head7 = (t) => ({ text: t, options: { bold: true, color: "FFFFFF", fill: { color: THEME.colors.dk2 } } });
  const rules7 = [
    ["Mismatch we saw", "Rule we found", "Rows"],
    ["Swiss payouts without tax still have a base", "Base = amount paid in CHF; elsewhere 0.00; no date without tax", "33"],
    ["31 Dec 2017 vs 3 Jan 2018", "A deadline on a closed day moves to the next business day (2 January closed)", "6"],
    ["Italian tax above 26 %", "Each rate on the gain earned while it was valid (2012, 2014 rate changes)", "10"],
    ["German tax 28.71, not 29.36", "Capital gains tax reduced by church tax, cents cut off", "3"],
    ["Italian duty one day short", "Days up to and including the payout day, over the days of that year", "7"],
    ["One cent off in 2019", "The 2019 correction is one booking, rounded once", "4"],
    ["A tax in the wrong year", "A withheld tax counts in the year it was paid to the tax office", "5"],
  ];
  s.addTable(rules7.map((r, i) => i === 0 ? r.map(head7) : r.map((t) => ({ text: t }))), {
    x: 0.5, y: 1.15, w: 9.0, colW: [3.1, 5.2, 0.7], fontSize: 12, fontFace: THEME.bodyFontFace, color: THEME.colors.dk1,
    border: { type: "solid", pt: 0.5, color: "C9D2DC" }, fill: { color: "FFFFFF" }, rowH: 0.42, valign: "middle", objectName: "t7 rules table",
  });
  s.addNotes(
    "This is the core of the method. Each wrong row in the published samples pointed to one specific rule. " +
    "Swiss payouts without tax still report the amount paid as base. A deadline on a weekend or holiday moves to the next business day, and in Switzerland 2 January is closed. " +
    "Italian tax above 26 percent showed that the rate changes of 2012 and 2014 split the gain. German church members pay less capital gains tax, and German cents are cut off. " +
    "Each rule was kept only if it held on every one of the 110 sample rows."
  );

  // 10 t7: the Italian split, one real payout ---------------------------------------------------------------------
  s = pres.addSlide({ masterName: "Content", sectionTitle: "Surprise t7" });
  s.addText("The Italian tax, period by period", { placeholder: "title" });
  s.addImage({ path: PLOT("t7_italian_split.png"), x: 0.75, y: 1.05, w: 8.5, h: 8.5 * 770 / 1680, altText: "Policy value and premiums of BL10001596 with the three Italian rate periods", objectName: "Italian split plot" });
  s.addNotes(
    "Here is one real payout. The policy started in 2009, and Italy taxed its gain at 12.5, then 20, then 26 percent. " +
    "Neuron does not apply today's rate to the whole gain: it values the policy on the last day of each rate period and taxes each part of the gain at the rate of its period. " +
    "So this 15 percent withdrawal pays 847 euros, not the 1,356 of a flat 26 percent, exactly as in the audit sample."
  );

  // 11 t7: results ---------------------------------------------------------------------------------------------------
  s = pres.addSlide({ masterName: "Content", sectionTitle: "Surprise t7" });
  s.addText("t7 results: annual 11 → 29 of 30", { placeholder: "title" });
  s.addImage({ path: PLOT("t7_score_progression.png"), x: 0.5, y: 1.05, w: 6.4, h: 6.4 * 700 / 1680, altText: "t7 leaderboard accuracy per upload", objectName: "Score progression plot" });
  const numbers7 = [["29 / 30", "annual rows on the leaderboard"], ["109 / 110", "published sample rows exact (one off by a cent)"], ["88.80 %", "average accuracy, from 77.01 %"]];
  numbers7.forEach(([value, label], i) => {
    const y = 1.1 + i * 1.25;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 7.1, y, w: 2.4, h: 1.1, rectRadius: 0.08, fill: { color: C.background2 }, line: { color: C.background2 }, objectName: `t7 result card ${i + 1}` });
    s.addText(value, { x: 7.25, y: y + 0.08, w: 2.1, h: 0.5, fontSize: 24, bold: true, fontFace: THEME.headFontFace, color: C.accent3, margin: 0, isTextBox: true, objectName: `t7 result value ${i + 1}` });
    s.addText(label, { x: 7.25, y: y + 0.6, w: 2.1, h: 0.45, fontSize: 11, color: C.text2, margin: 0, isTextBox: true, objectName: `t7 result label ${i + 1}` });
  });
  s.addText("The leaderboard credits our dated payout rows; the undated ones we match exactly in the published samples are not credited there.", { x: 0.5, y: 4.1, w: 6.4, h: 0.75, fontSize: 11, italic: true, color: C.text2, margin: 0, isTextBox: true, objectName: "t7 caveat" });
  s.addNotes(
    "The effect on the leaderboard: the annual table went from 11 to 29 of 30 rows, and our average from 77 to almost 89 percent. " +
    "On the two samples the organisers published we match every one of the 110 rows, one of them off by a single cent. " +
    "One honest caveat: the leaderboard credits only our payout rows that carry a remittance date; the undated rows we match exactly in the published samples are not credited there."
  );

  // 12 t7: where the samples are silent --------------------------------------------------------------------------
  s = pres.addSlide({ masterName: "Content", sectionTitle: "Surprise t7" });
  s.addText("Where the samples are silent, the law decides", { placeholder: "title" });
  s.addImage({ path: PLOT("t7_sample_coverage.png"), x: 0.4, y: 1.1, w: 6.0, h: 6.0 * 840 / 1820, altText: "Payout patterns and how many the published samples checked", objectName: "Sample coverage plot" });
  s.addText([
    { text: "Red cells: patterns no sample ever checked", options: { bullet: true, breakLine: true } },
    { text: "Swiss tax is due 30 days after the end of the month (Art. 16 VStG)", options: { bullet: true, breakLine: true } },
    { text: "Dates count from the month the money was paid (PD_PAYDAY, the one field no other task uses)", options: { bullet: true, breakLine: true } },
    { text: "Each choice keeps all 110 sample rows exact", options: { bullet: true } },
  ], { x: 6.6, y: 1.15, w: 3.0, h: 3.6, fontSize: 13, color: C.text1, paraSpaceAfter: 8, valign: "top", margin: 0, isTextBox: true, objectName: "Law bullets" });
  s.addNotes(
    "The samples covered only part of the patterns: the red cells here were never checked. " +
    "There we let the law decide, as long as every sample row stays exact: Swiss withholding tax is due thirty days after the end of the month, " +
    "and deadlines count from the month the money was paid, using the payout days of the product table, the one field no other task uses."
  );

  // 13 Closing ------------------------------------------------------------------------------------------------------
  pres.addSection({ title: "Closing" });
  s = pres.addSlide({ masterName: "Title dark", sectionTitle: "Closing" });
  logoCard(s, pres, C, 0.6, 0.45, 2.6, 1.55);
  s.addText("Thank you", { placeholder: "title" });
  s.addText("Questions are welcome", { placeholder: "body" });
  s.addText("TEAM NAMA", { x: 0.6, y: 4.1, w: 4, h: 0.35, fontSize: 14, bold: true, color: C.accent1, charSpacing: 2, margin: 0, isTextBox: true, objectName: "Team name" });
  s.addText(MEMBERS, { x: 0.6, y: 4.45, w: 8.8, h: 0.4, fontSize: 16, color: C.background1, margin: 0, isTextBox: true, objectName: "Members" });
  s.addNotes(
    "To sum up: no model runs in our submission, every rule is plain code backed by an exact test, " +
    "and the discovery tools know nothing about insurance, so they are ready for the next migration. Thank you, we are happy to take your questions."
  );

  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("written", OUT, LOGO ? "with logo" : "WITHOUT logo (save usi_logo.png next to this script)");
}

main().catch((e) => { console.error(e); process.exit(1); });
