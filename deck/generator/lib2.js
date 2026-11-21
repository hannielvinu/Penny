// Pitch-deck design system: 16:9, Poppins display, Inter body, shape-built diagrams.
const pptxgen = require("pptxgenjs");
const { imageSize } = require("./imgsize");

function deck(T) {
  const pptx = new pptxgen();
  pptx.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
  const H = "Poppins", B = "Inter";
  const X = { pptx, T, H, B };
  let n = 0;

  X.slide = (dark = false) => {
    n += 1;
    const s = pptx.addSlide();
    s.background = { color: dark ? T.dark : T.bg };
    if (!dark) {
      s.addText(T.footer, { x: 0.55, y: 7.05, w: 9, h: 0.28, fontFace: B, fontSize: 9, color: T.muted });
      s.addText(String(n).padStart(2, "0"), { x: 12.2, y: 7.05, w: 0.6, h: 0.28, fontFace: H, fontSize: 9, bold: true, color: T.primary, align: "right" });
    }
    return s;
  };

  X.head = (s, kicker, title, o = {}) => {
    s.addShape(pptx.ShapeType.rect, { x: 0.55, y: 0.5, w: 0.5, h: 0.07, fill: { color: T.accent }, line: { color: T.accent } });
    s.addText(kicker.toUpperCase(), { x: 1.15, y: 0.36, w: 10, h: 0.35, fontFace: B, fontSize: 11, bold: true, color: o.dark ? T.accent2 : T.primary, charSpacing: 3 });
    s.addText(title, { x: 0.55, y: 0.78, w: o.w || 12.2, h: 0.9, fontFace: H, fontSize: o.size || 32, bold: true, color: o.dark ? "FFFFFF" : T.ink, valign: "top", fit: "shrink" });
  };

  X.t = (s, text, x, y, w, h, o = {}) =>
    s.addText(text, { x, y, w, h, fontFace: o.font || B, fontSize: o.size || 15, color: o.color || T.ink, bold: !!o.bold, italic: !!o.italic, align: o.align || "left", valign: o.valign || "top", fit: "shrink", lineSpacingMultiple: o.ls || 1.05, charSpacing: o.cs || 0, paraSpaceAfter: o.psa || 0 });

  X.box = (s, x, y, w, h, o = {}) =>
    s.addShape(o.round === false ? pptx.ShapeType.rect : pptx.ShapeType.roundRect, { x, y, w, h, rectRadius: o.r || 0.14, fill: { color: o.fill || T.card }, line: { color: o.line || o.fill || T.line, width: o.lw || 1 }, shadow: o.shadow ? { type: "outer", blur: 8, offset: 3, angle: 90, color: "000000", opacity: 0.12 } : undefined });

  X.pill = (s, text, x, y, o = {}) => {
    const w = o.w || 0.16 + text.length * (o.size || 11) * 0.0095;
    X.box(s, x, y, w, o.h || 0.34, { fill: o.fill || T.primary, r: 0.17 });
    X.t(s, text, x, y, w, o.h || 0.34, { size: o.size || 11, bold: true, color: o.color || "FFFFFF", align: "center", valign: "middle" });
    return w;
  };

  X.dot = (s, label, x, y, d, o = {}) => {
    s.addShape(pptx.ShapeType.ellipse, { x, y, w: d, h: d, fill: { color: o.fill || T.primary }, line: { color: o.fill || T.primary } });
    X.t(s, label, x, y, d, d, { font: H, size: o.size || 16, bold: true, color: o.color || "FFFFFF", align: "center", valign: "middle" });
  };

  X.arrow = (s, x1, y1, x2, y2, o = {}) =>
    s.addShape(pptx.ShapeType.line, { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1) || 0.001, h: Math.abs(y2 - y1) || 0.001, flipH: x2 < x1, flipV: y2 < y1, line: { color: o.color || T.primary, width: o.w || 2.25, endArrowType: "triangle", dashType: o.dash || "solid" } });

  // Screenshot inside a browser chrome frame, fitted into (x,y,w,h) keeping aspect.
  X.browser = (s, path, x, y, w, h, o = {}) => {
    const [iw, ih] = imageSize(path);
    const bar = 0.32;
    const sc = Math.min(w / iw, (h - bar) / ih);
    const fw = iw * sc, fh = ih * sc;
    const fx = x + (w - fw) / 2, fy = y + (h - bar - fh) / 2;
    X.box(s, fx - 0.04, fy - 0.04, fw + 0.08, fh + bar + 0.08, { fill: o.frame || "FFFFFF", line: o.edge || T.line, r: 0.1, shadow: true });
    ["FF5F57", "FEBC2E", "28C840"].forEach((c, i) => s.addShape(pptx.ShapeType.ellipse, { x: fx + 0.12 + i * 0.18, y: fy + 0.1, w: 0.11, h: 0.11, fill: { color: c }, line: { color: c } }));
    if (o.url) X.t(s, o.url, fx + 0.75, fy + 0.04, fw - 0.9, 0.24, { size: 8.5, color: T.muted });
    s.addImage({ path, x: fx, y: fy + bar, w: fw, h: fh });
    return { fx, fy, fw, fh: fh + bar };
  };

  X.big = (s, num, label, x, y, w, o = {}) => {
    X.t(s, num, x, y, w, o.h || 1.0, { font: H, size: o.size || 54, bold: true, color: o.color || T.primary, valign: "bottom" });
    X.t(s, label, x, y + (o.h || 1.0) + 0.05, w, o.lh || 0.75, { size: o.lsize || 13.5, color: o.lcolor || T.ink });
  };

  // Paired horizontal bars: rows [{label, a, b, max, fa, fb}]
  X.bars = (s, rows, x, y, w, rowH, legend) => {
    const lw = 2.6, bw = w - lw - 1.0;
    X.t(s, [{ text: "■ ", options: { color: T.primary } }, { text: legend[0] + "     " }, { text: "■ ", options: { color: "A8AFB8" } }, { text: legend[1] }], x, y - 0.42, w, 0.3, { size: 11 });
    rows.forEach((r, i) => {
      const ry = y + i * rowH;
      X.t(s, r.label, x, ry, lw - 0.15, rowH - 0.1, { size: 12.5, valign: "middle", bold: !!r.bold });
      [[r.a, T.primary, r.fa, 0], [r.b, "A8AFB8", r.fb, 1]].forEach(([v, c, f, k]) => {
        const by = ry + 0.08 + k * 0.3, bl = Math.max(0.04, (bw * v) / r.max);
        s.addShape(pptx.ShapeType.rect, { x: x + lw, y: by, w: bl, h: 0.24, fill: { color: c }, line: { color: c } });
        X.t(s, f, x + lw + bl + 0.08, by - 0.04, 1.2, 0.32, { size: 11.5, bold: k === 0, valign: "middle" });
      });
    });
  };

  X.save = (p) => pptx.writeFile({ fileName: p });
  return X;
}
module.exports = { deck };
