"""Builds the README figures in assets/ from scoreboard.json (and the real output of show.py)."""
import json
import subprocess
import sys
import numpy as np
from matplotlib.patches import Rectangle
from figstyle import *

P = theme("crimson")
S = json.load(open("scoreboard.json"))
MODELS = S["models"]
MLAB = {"qwen2.5-0.5b": "qwen 2.5 0.5b", "llama3.2-1b": "llama 3.2 1b", "qwen2.5-1.5b": "qwen 2.5 1.5b"}
ARMS = [("none", "no defence", 1.0, "acc"), ("spotlight", "spotlighting", 0.6, "acc"), ("hierarchy", "hierarchy", 0.38, "acc"),
        ("both", "both", 0.2, "acc"), ("none+output_filter", "output filter", 0.25, "fg")]
CHL = {"clean": "clean (control)", "visible_text": "visible text", "html_comment": "html comment",
       "fake_system_note": "fake 'system' note", "doc_footer": "document footer", "image_alt_text": "image alt text"}


def cell(m, arm, key="injected_all"):
    return S["cells"][m].get(arm, {}).get(key)


# 0. banner: a document page whose hidden line leaks out to the right as a stream
rng = np.random.default_rng(13)
field = np.full((100, 400), 0.04)
field[10:90, 150:250] = 0.12                                   # the page
for r in range(18, 86, 6):
    field[r:r + 2, 160:160 + int(rng.integers(45, 82))] = 0.55   # lines of text
field[54:56, 160:238] = 1.0                                    # the hidden instruction
for c in range(240, 400):
    t = (c - 240) / 160
    for _ in range(3):
        rr = int(55 + rng.normal(0, 2 + 10 * t))
        if 0 <= rr < 100 and rng.random() < 0.9 - 0.6 * t:
            field[rr, c] = 1.0
banner("banner.png", "agent-injection-range",
       "hidden text in a document tries to hijack a small tool-using agent.", field,
       meta="> defensive · 3 small open models · cpu only")

# 1. hijack rate per model and defence
f, ax = fig(6.4, bottom_in=1.6)
x = np.arange(len(MODELS)); w = 0.16
for k, (arm, lab, lv, ramp) in enumerate(ARMS):
    for i, m in enumerate(MODELS):
        c = cell(m, arm)
        v = 100 * c["hijack"] / c["n"]
        xi = x[i] + (k - 2) * w
        dbar(ax, xi, max(v, 0.6), lv, ramp, width=w * 0.86)
        label(ax, xi, v + 2, str(c["hijack"]), color=getattr(P, ramp), ha="center", va="bottom", fontsize=11.5)
ax.set_xticks(x); ax.set_xticklabels([MLAB[m] for m in MODELS])
ax.set_ylim(0, 92); ax.set_yticks([0, 25, 50, 75]); ax.set_ylabel("% of 120 poisoned runs hijacked")
ax.grid(axis="x", visible=False)
ax.legend(handles=[swatch(lv, ramp, lab) for _, lab, lv, ramp in ARMS], loc="upper center",
          bbox_to_anchor=(0.5, -0.16), ncol=5, fontsize=12)
title(ax, "a poisoned document hijacked llama 3.2 1b in 56% of runs",
      "and on llama the prompt defences made it worse · clean documents: 0 hijacks · the filter's 0 is by design")
save(f, "hijack-by-defence.png")

# 2. which hiding spot works, per model (no defence) and pooled per defence
cols = [(MLAB[m].rsplit(" ", 1)[0] + "\n" + MLAB[m].rsplit(" ", 1)[1], m, "none") for m in MODELS] + [("all\nnone", "all", "none"), ("all\nspotlight", "all", "spotlight"),
                                                  ("all\nhierarchy", "all", "hierarchy"), ("all\nboth", "all", "both")]
chans = S["channels"]
f, ax = fig(7.4, left=0.24, right=0.97, top_in=1.85, bottom_in=0.4)
for j, (lab, m, arm) in enumerate(cols):
    for i, ch in enumerate(chans):
        c = S["cells"][m].get(arm, {}).get(ch)
        if not c:
            continue
        r = c["hijack"] / c["n"]
        ax.add_patch(Rectangle((j - 0.46, i - 0.44), 0.92, 0.88, facecolor=D(max(r, 0.04)), edgecolor="none"))
        label(ax, j, i, f"{c['hijack']}/{c['n']}", ha="center", va="center", boxed=True, fontsize=11.5,
              color=P.acc if r >= 0.25 else P.fg, fontweight="bold" if r >= 0.25 else "normal")
ax.axvline(len(MODELS) - 0.5, color=P.fg, lw=2)
ax.set_xlim(-0.55, len(cols) - 0.45); ax.set_ylim(len(chans) - 0.45, -0.55)
ax.set_xticks(range(len(cols))); ax.set_xticklabels([c[0] for c in cols], fontsize=11.5)
ax.xaxis.tick_top()
ax.set_yticks(range(len(chans))); ax.set_yticklabels([CHL[c] for c in chans])
ax.grid(False); ax.tick_params(length=0)
for s_ in ax.spines.values():
    s_.set_visible(False)
head(f, "which hiding spot works, on which model?",
     "hijacked runs · left: each model with no defence · right: all models pooled, per defence", y_in=0.25)
save(f, "hiding-spots.png")

# 3. the real terminal readout
out = subprocess.run([sys.executable, "-c", "import runpy; runpy.run_path('./show.py', run_name='__main__')"],
                     capture_output=True, text=True, encoding="utf8", check=True).stdout
term_capture("show.png", "python show.py", out)
