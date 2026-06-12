"""Erzeugt den 2D-Grundriss (grundriss.png) aus den Chat-Maßen.

Koordinaten in cm: x entlang Wand A (0 = Ecke D/A), y von Wand A Richtung Wand C.
"""
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

# Schacht in Ecke A/B (rechts an Wand A)
ax.add_patch(Rectangle((A - SCHACHT_X, 0), SCHACHT_X, SCHACHT_Y, facecolor="#888", zorder=2))
ax.annotate("Schacht\n15×48", (A - SCHACHT_X - 5, SCHACHT_Y + 8), fontsize=8, ha="right")

# Tür in Wand C (Maß ab Wand B)
door_x0 = A - DOOR_FROM_B - DOOR_W
ax.add_patch(Rectangle((door_x0, B - 2), DOOR_W, WALL + 4, facecolor="#fff", edgecolor="none", zorder=3))
ax.plot([door_x0, door_x0], [B, B - DOOR_W], color="#b5651d", zorder=4)
ax.add_patch(plt.matplotlib.patches.Arc((door_x0, B), 2*DOOR_W, 2*DOOR_W,
             theta1=270, theta2=360, color="#b5651d", linestyle=":", zorder=4))
ax.annotate(f"Tür 95\n(60 ab Wand B)", (door_x0 + DOOR_W/2, B - 50), fontsize=8, ha="center")

# Fenster in Wand D (x=0); Maß ab Wand C
win_y0 = WIN_TO_A
ax.add_patch(Rectangle((-WALL, win_y0), WALL, WIN_W, facecolor="#aee", edgecolor="#37c", zorder=3))
ax.annotate(f"Fenster {WIN_W}\n(22 zu A, 120 zu C)", (18, win_y0 + WIN_W/2), fontsize=8, va="center")

def moebel(x, y, w, h, label, color="#cdd8e3", rot_label=False):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=color, edgecolor="#456", zorder=2))
    ax.annotate(label, (x + w/2, y + h/2), fontsize=7.5, ha="center", va="center",
                rotation=90 if rot_label else 0)

# --- Möbel: ENTWURF (Positionen geschätzt, Video-Abgleich offen) ---
moebel(40, 0, 200, 90, "Hochbett 200×90 (H160)\nPosition geschätzt", "#e3d5cd")
moebel(A - 65, SCHACHT_Y, 65, 100, "Schrank\n100×65\n(H237)", "#eee", True)         # Wand B, nach Schacht
ax.add_patch(Rectangle((A - 65, SCHACHT_Y + 100), 65, 15, facecolor="#ffd", edgecolor="#a90", zorder=2))
ax.annotate("Spalt 10–20\n(Besen/Werkzeug)", (A - 72, SCHACHT_Y + 107), fontsize=7, ha="right", va="center")
moebel(A - 38, SCHACHT_Y + 125, 38, 110, "IKEA-Regal\nT38 (B/H?)", "#d5e3cd", True)
moebel(172, B - 50, 80, 50, "Kommode weiß\n80×50 (H78)")
moebel(88, B - 50, 80, 50, "Kommode weiß\n80×50 (H78)")
moebel(46, B - 50, 40, 50, "türkis\n40×50", "#b8e8e0")
moebel(4, B - 50, 40, 50, "türkis\n40×50", "#b8e8e0")

# Kleiderstangen (auf 270 Höhe, über dem Bett) + Klimmzugstange parallel Wand A
ax.plot([50, 140], [30, 30], color="#937", lw=3, zorder=5)
ax.plot([150, 240], [30, 30], color="#937", lw=3, zorder=5)
ax.annotate("2 Kleiderstangen @H270 (übers Bett)", (145, 38), fontsize=7.5, ha="center", color="#937")
ax.plot([250, 350], [22, 22], color="#333", lw=3, zorder=5)
ax.annotate("Klimmzugstange (parallel zu A, Position?)", (300, 30), fontsize=7.5, ha="center")

# Wandbeschriftung + Maßketten
ax.annotate("Wand A — 414", (A/2, -30), ha="center", fontsize=11, weight="bold")
ax.annotate("Wand B — 300", (A + 30, B/2), va="center", fontsize=11, weight="bold", rotation=90)
ax.annotate("Wand C — 414 (Rest rechts neben Tür: 259)", (A/2, B + 28), ha="center", fontsize=11, weight="bold")
ax.annotate("Wand D — 300 (Fenster)", (-32, B/2), va="center", fontsize=11, weight="bold", rotation=90)

ax.set_xlim(-70, A + 70); ax.set_ylim(-70, B + 70)
ax.set_aspect("equal"); ax.invert_yaxis(); ax.axis("off")
ax.set_title("Grundriss-Entwurf (cm) — Raumgeometrie fix, Möbelpositionen geschätzt", fontsize=12)
plt.tight_layout()
plt.savefig("/home/user/dimitrisakritidis.github.io/renovierung/grundriss.png", dpi=150)
print("ok")
