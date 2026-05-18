import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Tuple
from .models import StrategyEvaluation

def create_charts(evals: List[StrategyEvaluation]) -> Tuple[str, str]:
    """Draw the bar and line charts."""
    bg, text = "none", "#1e293b"
    colors = ["#64748b", "#0284c7", "#16a34a", "#ea580c"]

    plt.rcParams.update({
        "figure.facecolor": bg, "axes.facecolor": bg, "text.color": text,
        "axes.labelcolor": text, "xtick.color": text, "ytick.color": text,
        "axes.edgecolor": "#94a3b8", "grid.color": "#cbd5e1", "font.family": "sans-serif"
    })

    # 1. Bar Chart
    fig1, ax1 = plt.subplots(figsize=(8, 4))
    names = [e.Strategy.capitalize() for e in evals]
    yields = [e.HarvestAmount for e in evals]
    ax1.bar(names, yields, color=colors)
    ax1.set_ylabel("Yield (kg/ha)")
    
    buf1 = io.BytesIO()
    fig1.savefig(buf1, format="png", bbox_inches="tight", transparent=True)
    plot1 = base64.b64encode(buf1.getvalue()).decode()
    plt.close(fig1)

    # 2. Line Chart
    fig2, ax2 = plt.subplots(figsize=(8, 4))
    x_pos = [0, 2, 4, 8]
    x_labels = ["Now", "Week 2", "Week 4", "Week 8"]
    
    for i, e in enumerate(evals):
        y = [e.YieldCurve[w] for w in x_pos]
        try:
            from scipy.interpolate import make_interp_spline
            spline = make_interp_spline(x_pos, y, k=2)
            x_smooth = np.linspace(0, 8, 50)
            ax2.plot(x_smooth, spline(x_smooth), color=colors[i % 4], label=e.Strategy.capitalize(), lw=2.5)
            ax2.plot(x_pos, y, 'o', color=colors[i % 4])
        except:
            ax2.plot(x_pos, y, '-o', color=colors[i % 4], label=e.Strategy.capitalize())

    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(x_labels)
    ax2.set_ylabel("Yield %")
    ax2.set_ylim(0, 110)
    ax2.legend()
    
    buf2 = io.BytesIO()
    fig2.savefig(buf2, format="png", bbox_inches="tight", transparent=True)
    plot2 = base64.b64encode(buf2.getvalue()).decode()
    plt.close(fig2)

    return plot1, plot2
