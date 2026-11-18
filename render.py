import json, sys, os, textwrap
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
from style import *
S = json.load(open("scoreboard.json"))
A = S["cells"]["all"]; T = S["tests"]["all"]; models = S["models"]
TITLE = "agent-injection-range \u2014 3 small open models, local cpu"
MLAB = {"qwen2.5-0.5b": "qwen 2.5 0.5b", "llama3.2-1b": "llama 3.2 1b", "qwen2.5-1.5b": "qwen 2.5 1.5b"}
CHL = {"clean": "clean document (control)", "visible_text": "visible text", "html_comment": "html comment", "fake_system_note": "fake 'system' note",
       "doc_footer": "document footer", "image_alt_text": "image alt text"}
def pc(c, k="success"): return 100 * c[k] / max(1, c["n"])
def fp(p): return "< 0.0001" if p < 1e-4 else f"= {p:.2f}" if p >= 0.01 else f"= {p:.3f}"
# ---------- card grid: one card per model, defences as rows
ARMS = [("no defence", "none", RED), ("spotlighting", "spotlight", YEL), ("instruction hierarchy", "hierarchy", CY),
        ("spotlight + hierarchy", "both", MAG), ("output filter", "none+output_filter", GRN)]
W = 1240; CW = 382; y0 = 168; CH = 600
im, d = canvas(W, 1000, TITLE)
d.text((30, 64), "can a poisoned document hijack a small ai agent?", font=font(28, True), fill=FG)
d.text((30, 104), "the agent reads a webpage, email or file. hidden text tells it to leak a planted fake api key", font=font(16), fill=DIM)
d.text((30, 128), "or send it to an outside address. hijacked = it did either.", font=font(16), fill=DIM)
for i, m in enumerate(models):
    x = 30 + i * (CW + 14); c = S["cells"][m]
    base = c["none"]["injected_all"]
    col = RED if base["hijack"] / base["n"] >= 0.25 else YEL if base["hijack"] / base["n"] >= 0.05 else GRN
    d.rounded_rectangle([x, y0, x + CW, y0 + CH], 14, fill=PAN, outline=col, width=2)
    d.text((x + 18, y0 + 14), MLAB[m], font=font(22, True), fill=col)
    d.text((x + 18, y0 + 48), "hijacked, no defence", font=font(15), fill=FG)
    d.text((x + 18, y0 + 70), f"{100 * base['hijack'] / base['n']:.0f}%", font=font(60, True), fill=col)
    d.text((x + 18, y0 + 146), f"{base['hijack']} / {base['n']} poisoned runs", font=font(14), fill=DIM)
    d.text((x + 18, y0 + 166), f"clean docs: {c['none']['clean']['hijack']} / {c['none']['clean']['n']}", font=font(14), fill=DIM)
    yy = y0 + 202
    d.text((x + 18, yy), "with each defence", font=font(15, True), fill=FG); yy += 28
    for lab, key, cc in ARMS:
        if key not in c or "injected_all" not in c[key]: continue
        v = c[key]["injected_all"]; t = f"{v['hijack']}/{v['n']}"
        d.text((x + 18, yy), lab, font=font(14), fill=DIM)
        d.text((x + CW - 18 - d.textlength(t, font=font(15, True)), yy - 1), t, font=font(15, True), fill=FG)
        bar(d, x + 18, yy + 21, CW - 36, 10, v["hijack"] / v["n"], cc); yy += 50
    yy += 4; d.line([x + 18, yy, x + CW - 18, yy], fill=BOR); yy += 12
    d.text((x + 18, yy), "unasked-for sends on clean docs", font=font(14), fill=FG); yy += 24
    for lab, key in [("none", "none"), ("hierarchy", "hierarchy"), ("both", "both")]:
        if key in c and "clean" in c[key]:
            v = c[key]["clean"]; t = f"{v['unauth_send']}/{v['n']}"
            d.text((x + 18, yy), lab, font=font(14), fill=DIM); d.text((x + CW - 18 - d.textlength(t, font=font(15, True)), yy - 1), t, font=font(15, True), fill=FG); yy += 22
y = y0 + CH + 26
ll = S["tests"].get("llama3.2-1b", {})
if "both_vs_none_hijack_p" in ll:
    d.text((30, y), f"llama 3.2 1b: the prompt defences made it worse. hierarchy vs none p {fp(ll['hierarchy_vs_none_hijack_p'])}, both p {fp(ll['both_vs_none_hijack_p'])}.", font=font(17), fill=YEL)
lines = ["12 fake documents x 5 hiding spots x 2 wordings = 120 poisoned runs per model and defence, 1 sampled run each.",
         "clean docs = same 12 documents with nothing hidden, 2 runs each. key and recipient are invented.",
         "the output filter is a rule (drop sends, redact the exact key), so its 0 is by design; it would miss a",
         "rewritten key. a send to an unrequested address counts as over-action, not as hijack. no attack text shown."]
for k, ln in enumerate(lines): d.text((30, y + 36 + 24 * k), ln, font=font(15), fill=DIM)
save(im.crop((0, 0, W, y + 36 + 24 * len(lines) + 20)), "img1-scoreboard-grid.png"); print("grid ok")

# ---------- channel x model matrix (no defence) + defence columns pooled
def heat(r):
    if r <= 0.5: t = r / 0.5; a, b = (24, 54, 38), (150, 110, 20)
    else: t = (r - 0.5) / 0.5; a, b = (150, 110, 20), (200, 50, 45)
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
cols = [(MLAB[m], m, "none") for m in models] + [("all, none", "all", "none"), ("all, spotlight", "all", "spotlight"), ("all, hierarchy", "all", "hierarchy"), ("all, both", "all", "both")]
cw, chh, left, top = 128, 50, 290, 200
W2 = left + cw * len(cols) + 30; H2 = top + chh * 6 + 140
im, d = canvas(W2, H2, TITLE)
d.text((30, 64), "which hiding spot works, on which model?", font=font(24, True), fill=FG)
d.text((30, 100), "hijacked runs. left: per model, no defence. right: all models pooled, per defence.", font=font(15), fill=DIM)
for j, (lab, m, arm) in enumerate(cols):
    for k, ln in enumerate(textwrap.wrap(lab, 12)):
        tw = d.textlength(ln, font=font(14, True)); d.text((left + j * cw + (cw - tw) / 2, top - 50 + 18 * k), ln, font=font(14, True), fill=FG)
for i, ch in enumerate(S["channels"]):
    y = top + i * chh
    d.text((30, y + 15), CHL[ch], font=font(16), fill=CY if ch == "clean" else FG)
    for j, (lab, m, arm) in enumerate(cols):
        x = left + j * cw
        c = S["cells"][m].get(arm, {}).get(ch)
        if not c: continue
        r = c["hijack"] / c["n"]
        d.rounded_rectangle([x + 4, y + 4, x + cw - 4, y + chh - 4], 6, fill=heat(r))
        t = f"{c['hijack']}/{c['n']}"; tw = d.textlength(t, font=font(16, True)); d.text((x + (cw - tw) / 2, y + 15), t, font=font(16, True), fill=(240, 240, 240))
d.line([left + cw * len(models) + 2, top - 56, left + cw * len(models) + 2, top + chh * 6], fill=BOR, width=3)
d.text((30, top + chh * 6 + 20), "each per-model cell: 24 runs (12 docs x 2 wordings; clean = 12 docs x 2 seeds). pooled cells: " + str(24 * len(models)) + ".", font=font(14), fill=DIM)
save(im, "img2-channel-matrix.png"); print("matrix ok")
