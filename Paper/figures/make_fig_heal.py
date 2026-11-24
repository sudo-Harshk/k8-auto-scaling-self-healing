"""Fig. 5: self-healing fault runs, per-run values (results_live/heal_analysis/heal_per_run.csv)."""
import csv, statistics, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
rows=[r for r in csv.DictReader(open("results_live/heal_analysis/heal_per_run.csv")) if r["fault"]=="1"]
arms=[("shield-heal","SHIELD-AI\n(heal)"),("shield-heal-gated","SHIELD-AI\n(heal, gated)"),("shield-noheal","SHIELD-AI\n(no heal)"),("hpa","HPA")]
fig,axs=plt.subplots(1,2,figsize=(7.2,2.9),dpi=200)
for ax,(m,lab) in zip(axs,[("slo_viol_pct","Time over SLO after fault (%)"),("recovery_s","Time to recover (s)")]):
    for i,(a,_) in enumerate(arms):
        v=[float(r[m]) for r in rows if r["arm"]==a]
        c="#2a6fdb" if a=="shield-heal" else "#8a8f98"
        ax.scatter([i+(k-(len(v)-1)/2)*0.5/max(len(v),5) for k in range(len(v))],v,s=28,color=c,edgecolor="white",linewidth=1,zorder=3)
        md=statistics.median(v); ax.plot([i-0.25,i+0.25],[md,md],color="#222",lw=1.5,zorder=2)
    ax.set_xticks(range(4)); ax.set_xticklabels([l for _,l in arms],fontsize=7)
    ax.set_ylabel(lab,fontsize=8); ax.tick_params(axis="y",labelsize=7)
    ax.grid(axis="y",color="#e5e5e5",lw=0.6); ax.set_axisbelow(True)
    for s in ("top","right"): ax.spines[s].set_visible(False)
n={a:sum(r["arm"]==a for r in rows) for a,_ in arms}
fired=sum(r["arm"]=="shield-heal" and r["heals"]!="0" for r in rows)
fig.text(0.5,0.005,f"Dots: one run each (n = {n['shield-heal']}/{n['shield-heal-gated']}/{n['shield-noheal']}/{n['hpa']}); black bar: median. Heal fired in {fired}/{n['shield-heal']} heal runs, always on the frozen pod; 0 false heals in 15 fault-free runs.",ha="center",fontsize=6.5,color="#444")
fig.tight_layout(rect=(0,0.04,1,1)); fig.savefig("Paper/figures/fig_heal.png"); print("ok")
