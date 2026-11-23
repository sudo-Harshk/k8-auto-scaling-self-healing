import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
L = [("1. Telemetry", "Prometheus\n(5 s scrape)\n-> producer\n-> Kafka"),
     ("2. Streaming", "Kafka (KRaft)\n+ Faust\n15 s feature\nwindows"),
     ("3. ML decision", "River:\nHoeffding Adaptive\nTree (replicas)\nHalf-Space Trees\n(anomaly)"),
     ("4. Safety shield", "min/max clamp\nasymmetric step\ncooldown up 15 s,\ndown 60 s\n(TLA+ verified)"),
     ("5. Actuation", "Python operator\n(kubernetes client)\nre-checks shield\nscale / heal")]
fig, ax = plt.subplots(figsize=(11, 2.8)); ax.axis("off")
w, g = 1.9, 0.35
for i, (t, d) in enumerate(L):
    x = i * (w + g)
    c = "#f6d7a7" if i == 3 else "#dbe7f3"
    ax.add_patch(FancyBboxPatch((x, 0), w, 1.6, boxstyle="round,pad=0.03", fc=c, ec="#333"))
    ax.text(x + w/2, 1.38, t, ha="center", fontsize=10, weight="bold")
    ax.text(x + w/2, 0.6, d, ha="center", va="center", fontsize=8.5)
    if i < 4: ax.annotate("", (x + w + g, 0.8), (x + w, 0.8), arrowprops=dict(arrowstyle="->", lw=1.5))
ax.annotate("", (w/2, -0.05), (4*(w+g)+w/2, -0.05),
            arrowprops=dict(arrowstyle="->", lw=1, ls="--", connectionstyle="arc3,rad=-0.12"))
ax.text(2*(w+g)+w/2, -0.75, "feedback: new cluster state is observed in the next window", ha="center", fontsize=8, style="italic")
ax.set_xlim(-0.1, 5*(w+g)); ax.set_ylim(-0.95, 1.8)
plt.savefig("fig1_architecture.png", dpi=300, bbox_inches="tight")
