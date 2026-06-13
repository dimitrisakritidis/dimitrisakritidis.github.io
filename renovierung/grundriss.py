"""Erzeugt den 2D-Grundriss (grundriss.png) — Ziel-Layout nach Video-Abgleich 12.06.2026.

Koordinaten in cm: x entlang Wand A (0 = Ecke D/A), y von Wand A Richtung Wand C.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

A, B = 414, 300          # Wandlängen
SCHACHT_X, SCHACHT_Y = 15, 48
DOOR_FROM_B, DOOR_W = 60, 95
WIN_FROM_C, WIN_TO_A = 120, 22
WIN_W = B - WIN_FROM_C - WIN_TO_A   # 158
WALL = 12                # gezeichnete Wandstärke

fig, ax = plt.subplots(figsize=(11, 8.5))

# Wände als äußerer Rahmen
ax.add_patch(Rectangle((-WALL, -WALL), A + 2*WALL, B + 2*WALL, facecolor="#888", zorder=0))
ax.add_patch(Rectangle((0, 0), A, B, facecolor="#f5f0e8", zorder=1))

# Schacht in Ecke A/B (rechts an Wand A) — im Video nie sichtbar, Maß aus Chat
ax.add_patch(Rectangle((A - SCHACHT_X, 0), SCHACHT_X, SCHACHT_Y, facecolor="#888", zorder=2))
ax.annotate("Schacht\n15×48", (A - SCHACHT_X - 5, SCHACHT_Y + 8), fontsize=8, ha="right")

# Tür in Wand C (Maß ab Wand B; alte Kassettentür, Band links, öffnet nach innen)
door_x0 = A - DOOR_FROM_B - DOOR_W
ax.add_patch(Rectangle((door_x0, B - 2), DOOR_W, WALL + 4, facecolor="#fff", edgecolor="none", zorder=3))
ax.plot([door_x0, door_x0], [B, B - DOOR_W], color="#b5651d", zorder=4)
ax.add_patch(plt.matplotlib.patches.Arc((door_x0, B), 2*DOOR_W, 2*DOOR_W,
             theta1=270, theta2=360, color="#b5651d", linestyle=":", zorder=4))
ax.annotate("Tür 95\n(60 ab Wand B)", (door_x0 + DOOR_W/2, B - 52), fontsize=8, ha="center")

# Fenster in Wand D (x=0); Maß ab Wand C. Oberkante ~245 (Video-Schätzung), Heizkörper darunter
win_y0 = WIN_TO_A
ax.add_patch(Rectangle((-WALL, win_y0), WALL, WIN_W, facecolor="#aee", edgecolor="#37c", zorder=3))
ax.annotate(f"Fenster {WIN_W}\n(22 zu A, 120 zu C)\nOberkante ~245 (Video)", (20, win_y0 + WIN_W/2 + 28),
            fontsize=8, va="center")
ax.add_patch(Rectangle((0, win_y0 + 24), 9, 110, facecolor="#fbb", edgecolor="#c44", zorder=2))
ax.annotate("Heizkörper", (13, win_y0 + 79), fontsize=7, va="center", color="#c44")

def moebel(x, y, w, h, label, color="#cdd8e3", rot_label=False, angle=0):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=color, edgecolor="#456", zorder=2,
                           angle=angle, rotation_point="center"))
    ax.annotate(label, (x + w/2, y + h/2), fontsize=7.5, ha="center", va="center",
                rotation=90 if rot_label else 0)

# --- Ziel-Layout (Video-Abgleich 12.06.2026; Positionen = ENTWURF) ---

# Klappbett an Wand A („ganz ran"), rechtes Ende links neben der Klimmzugstange;
# Ecke D/A bleibt frei für den Fenster-Schreibtisch. Grundfläche Annahme 200×120
moebel(140, 0, 200, 120, "Klappbett 200×120 (Annahme)\nklappt hoch an Wand A (dann H≈160)", "#e3d5cd")

# 2 Kleiderstangen @H270 übers Bett
ax.plot([145, 235], [30, 30], color="#937", lw=3, zorder=5)
ax.plot([240, 330], [30, 30], color="#937", lw=3, zorder=5)
ax.annotate("2 Kleiderstangen @H270 (übers Bett)", (238, 40), fontsize=7.5, ha="center", color="#937")

# Großer weißer Schrank an Wand B nach dem Schacht + Spalt + 2 Werkzeug-Regale
moebel(A - 65, SCHACHT_Y, 65, 100, "Schrank\n100×65\n(H237)", "#eee", True)
ax.add_patch(Rectangle((A - 65, SCHACHT_Y + 100), 65, 18, facecolor="#ffd", edgecolor="#a90", zorder=2))
ax.annotate("Spalt 10–20 (Besen/Handfeger)", (A - 72, SCHACHT_Y + 109), fontsize=7, ha="right", va="center")
moebel(A - 40, SCHACHT_Y + 118, 40, 35, "2 Regale\nWerkzeug", "#d5e3cd")

# Klimmzugstange 200 Ø5 @H~240: Dübel an Wand A ↔ liegt auf dem Schrank (Ton 7:20)
ax.plot([A - 33, A - 33], [0, 200], color="#333", lw=3, zorder=5)
ax.annotate("Klimmzugstange 200 @H~240\n(Dübel Wand A ↔ auf Schrank)", (A - 45, 196), fontsize=7.5,
            ha="right", color="#333")

# Massageliege geklappt zwischen Wand A und Schrank (Ton 11:33)
moebel(A - 85, 8, 65, 30, "Massageliege\ngeklappt (H170)", "#9bc")

# Kallax 4×4 an Wand C — kreative Einheit; rechts 1-m-Ablage (immer frei) + Sitz
moebel(6, B - 39, 147, 39, "Kallax 4×4 — 147×39 (H147)\nkreative Einheit (16 Fächer)", "#efe3cf")
moebel(160, B - 50, 100, 50, "1-m-Ablage\n(immer frei)", "#e8d9b0")
moebel(195, B - 105, 42, 42, "Sitz", "#d5e3cd")

# Fenster-Schreibtisch: 2 weiße Kommoden ~30° gedreht + gekürzte Platte (Zickzack-Entwurf)
moebel(8, 37, 80, 50, "Kommode weiß\n~30° gedreht", "#eee", angle=-30)
moebel(8, 137, 80, 50, "Kommode weiß\n~30° gedreht", "#eee", angle=30)
ax.annotate("Fenster-Schreibtisch (Zickzack-Entwurf):\nPlatte um 2 Bretter gekürzt,\n2 türkise Kommoden oben drauf",
            (95, 110), fontsize=7.5, ha="left", color="#a40")

# Bestand: OSB-Regale in der 60-cm-Nische zwischen Schrank und Tür
moebel(door_x0 + DOOR_W + 3, B - 30, 54, 30, "OSB-Regale\n(Nische 60)", "#e3dcc8")

# Elektrik (Video): Schalter+Steckdose neben Tür, 2 Doppel-Steckdosen Wand C, Steckdose Wand A kniehoch
for ex, ey in [(door_x0 - 12, B - 6), (100, B - 6), (195, B - 6), (A - 100, 2)]:
    ax.add_patch(Rectangle((ex, ey), 10, 5, facecolor="#fff", edgecolor="#c33", zorder=6))
ax.annotate("rot = Schalter/Steckdosen (Video)", (door_x0 - 14, B - 22), fontsize=7, ha="right", color="#c33")

# Wandbeschriftung + Maßketten
ax.annotate("Wand A — 414 (Bett)", (A/2, -30), ha="center", fontsize=11, weight="bold")
ax.annotate("Wand B — 300 (Schrank)", (A + 30, B/2), va="center", fontsize=11, weight="bold", rotation=90)
ax.annotate("Wand C — 414 (Tür; Rest neben Tür: 259 → Kallax + Ablage)", (A/2, B + 28), ha="center",
            fontsize=11, weight="bold")
ax.annotate("Wand D — 300 (Fenster + Schreibtisch)", (-32, B/2), va="center", fontsize=11,
            weight="bold", rotation=90)

ax.set_xlim(-70, A + 70); ax.set_ylim(-70, B + 70)
ax.set_aspect("equal"); ax.invert_yaxis(); ax.axis("off")
ax.set_title("Grundriss — Ziel-Layout nach Video-Abgleich 12.06.2026 (Möbelpositionen = Entwurf)", fontsize=12)
plt.tight_layout()
plt.savefig(Path(__file__).parent / "grundriss.png", dpi=150)
print("ok")
