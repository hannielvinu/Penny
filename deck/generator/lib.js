// Shared slide helpers: 16:9, Poppins headings, Inter body, shape-built diagrams.
const pptxgen = require("pptxgenjs");

function makeDeck(theme) {
  const pptx = new pptxgen();
  pptx.layout = "LAYOUT_WIDE"; // 13.33 x 7.5 in
  const T = theme;
  const H = "Poppins", B = "Inter";

  const api = { pptx, T };

  api.slide = (opts = {}) => {
    const s = pptx.addSlide();
    s.background = { color: opts.dark ? T.dark : T.bg };
    if (!opts.dark) {
      s.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 13.33, h: 0.12, fill: { color: T.primary }, line: { color: T.primary } });
      s.addText(T.footer, { x: 0.6, y: 7.0, w: 9, h: 0.3, fontFace: B, fontSize: 10, color: T.muted });
      if (opts.n) s.addText(String(opts.n), { x: 12.2, y: 7.0, w: 0.6, h: 0.3, fontFace: B, fontSize: 10, color: T.muted, align: "right" });
    }
    return s;
  };

  api.heading = (s, kicker, title) => {
    s.addText(kicker.toUpperCase(), { x: 0.6, y: 0.4, w: 12, h: 0.35, fontFace: B, fontSize: 12, bold: true, color: T.primary, charSpacing: 2 });
    s.addText(title, { x: 0.6, y: 0.75, w: 12.1, h: 0.95, fontFace: H, fontSize: 30, bold: true, color: T.ink, valign: "top", fit: "shrink" });
  };

  api.text = (s, text, x, y, w, h, o = {}) =>
    s.addText(text, { x, y, w, h, fontFace: B, fontSize: o.size || 16, color: o.color || T.ink, bold: !!o.bold, valign: o.valign || "top", align: o.align || "left", paraSpaceAfter: 6, fit: "shrink", ...o.extra });

  api.bullets = (s, items, x, y, w, h, size = 16) =>
    s.addText(items.map((t) => (typeof t === "string" ? { text: t, options: { bullet: { indent: 18 } } } : { text: t.text, options: { bullet: { indent: 18 }, bold: !!t.bold } })),
      { x, y, w, h, fontFace: B, fontSize: size, color: T.ink, valign: "top", paraSpaceAfter: 8, fit: "shrink" });

  api.card = (s, x, y, w, h, o = {}) =>
    s.addShape(pptx.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.12, fill: { color: o.fill || T.card }, line: { color: o.line || T.line, width: 1 } });

  api.stat = (s, x, y, w, h, big, small, color) => {
    api.card(s, x, y, w, h);
    s.addText(big, { x: x + 0.2, y: y + 0.15, w: w - 0.4, h: h * 0.5, fontFace: H, fontSize: 34, bold: true, color: color || T.primary, valign: "middle", fit: "shrink" });
    s.addText(small, { x: x + 0.2, y: y + h * 0.55, w: w - 0.4, h: h * 0.42, fontFace: B, fontSize: 13, color: T.ink, valign: "top", fit: "shrink" });
  };

  // Horizontal flow of boxes joined by arrows. steps: [{title, sub, tag}]
  api.flow = (s, steps, x, y, w, h, o = {}) => {
    const gap = 0.35, bw = (w - gap * (steps.length - 1)) / steps.length;
    steps.forEach((st, i) => {
      const bx = x + i * (bw + gap);
      api.card(s, bx, y, bw, h, { fill: st.fill || T.card, line: st.line || T.primary });
      if (st.tag) s.addText(st.tag, { x: bx + 0.1, y: y + 0.1, w: bw - 0.2, h: 0.3, fontFace: B, fontSize: 10, bold: true, color: st.tagColor || T.accent, align: "center" });
      s.addText(st.title, { x: bx + 0.1, y: y + 0.42, w: bw - 0.2, h: 0.55, fontFace: H, fontSize: o.titleSize || 15, bold: true, color: T.ink, align: "center", valign: "middle", fit: "shrink" });
      s.addText(st.sub, { x: bx + 0.12, y: y + 1.0, w: bw - 0.24, h: h - 1.1, fontFace: B, fontSize: o.subSize || 11.5, color: T.muted, align: "center", valign: "top", fit: "shrink" });
      if (i < steps.length - 1)
        s.addShape(pptx.ShapeType.line, { x: bx + bw + 0.03, y: y + h / 2, w: gap - 0.06, h: 0, line: { color: T.primary, width: 2, endArrowType: "triangle" } });
    });
  };

  // Horizontal comparison bars. rows: [{label, a, b, max, fmt}]
  api.bars = (s, rows, x, y, w, labels, o = {}) => {
    const rowH = o.rowH || 0.95, labelW = o.labelW || 3.4, barW = w - labelW - 1.3;
    s.addText([{ text: "■ ", options: { color: T.primary } }, { text: labels[0] + "    ", options: { color: T.ink } }, { text: "■ ", options: { color: T.muted } }, { text: labels[1], options: { color: T.ink } }],
      { x, y: y - 0.45, w, h: 0.35, fontFace: B, fontSize: 12 });
    rows.forEach((r, i) => {
      const ry = y + i * rowH;
      s.addText(r.label, { x, y: ry, w: labelW - 0.1, h: rowH - 0.15, fontFace: B, fontSize: 13, color: T.ink, valign: "middle", fit: "shrink" });
      [[r.a, T.primary, 0], [r.b, T.muted, 1]].forEach(([v, c, k]) => {
        const by = ry + 0.08 + k * 0.36;
        const bw = Math.max(0.05, (barW * v) / r.max);
        s.addShape(pptx.ShapeType.rect, { x: x + labelW, y: by, w: bw, h: 0.28, fill: { color: c }, line: { color: c } });
        s.addText(r.fmt(v, k), { x: x + labelW + bw + 0.08, y: by - 0.04, w: 1.4, h: 0.36, fontFace: B, fontSize: 12, bold: k === 0, color: T.ink, valign: "middle" });
      });
    });
  };

  api.save = async (path) => pptx.writeFile({ fileName: path });
  return api;
}

module.exports = { makeDeck };
