from __future__ import annotations

import csv
import argparse
import json
import math
import random
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from analysis.analyze_results import time_binned_goodput

SOURCE = ROOT / 'results' / 'summary' / 'run_summary.csv'
OUTPUT = ROOT / 'output' / 'pdf' / 'TA_Progress_Legacy_vs_Adaptive.pdf'
MODES = ('legacy', 'proposed')
LABELS = {'legacy': 'Legacy adaptive', 'proposed': 'Proposed adaptive'}
COLORS = {'legacy': '#E69F00', 'proposed': '#009E73'}
HATCHES = {'legacy': '//', 'proposed': 'xx'}
DEPTHS = ('depth15', 'depth1000')
DEPTH_LABEL = {'depth15': 'Receiver C depth: 15 m', 'depth1000': 'Receiver C depth: 1000 m'}
FOOTER = 'Interim progress: earlier held-out evaluation (20 paired seeds per depth). New 5% target evaluation is still in progress.'


def read_rows():
    with SOURCE.open(newline='', encoding='utf-8') as stream:
        rows = list(csv.DictReader(stream))
    rows = [r for r in rows if r['mode'] in MODES and 'evaluation' in Path(r['run_dir']).parts]
    for row in rows:
        for key in ('seed', 'packets_transmitted', 'packets_received'):
            row[key] = int(row[key])
        for key in ('pdr_pct', 'packet_loss_pct', 'ack_ratio_pct', 'average_rtt_ms',
                    'median_rtt_ms', 'timeout_ratio_pct', 'throughput_bps', 'average_interval_ms'):
            row[key] = float(row[key])
    expected = {(d, m, s) for d in DEPTHS for m in MODES for s in range(11, 31)}
    actual = {(r['depth_case'], r['mode'], r['seed']) for r in rows}
    if actual != expected:
        raise RuntimeError(f'Evaluation matrix mismatch: missing={sorted(expected-actual)}, extra={sorted(actual-expected)}')
    return rows


def bootstrap_ci(values, seed=20261026):
    rng = random.Random(seed)
    means = sorted(statistics.mean(rng.choices(values, k=len(values))) for _ in range(5000))
    return means[125], means[4874]


def grouped(rows, depth, mode, metric):
    return [r[metric] for r in rows if r['depth_case'] == depth and r['mode'] == mode]


def add_footer(fig, page):
    fig.text(0.01, 0.012, FOOTER, fontsize=7.5, color='#444444', ha='left')
    fig.text(0.99, 0.012, f'Page {page}', fontsize=7.5, color='#444444', ha='right')


def style_axis(ax):
    ax.grid(axis='y', alpha=0.25, linewidth=0.7)
    ax.spines[['top', 'right']].set_visible(False)


def bar_page(pdf, rows, metric, ylabel, title, page, zero=True):
    fig, axes = plt.subplots(1, 2, figsize=(11.69, 8.27))
    fig.subplots_adjust(left=0.07, right=0.985, bottom=0.16, top=0.89, wspace=0.13)
    fig.suptitle(title, fontsize=17, fontweight='bold')
    for ax, depth in zip(axes, DEPTHS):
        values = [statistics.mean(grouped(rows, depth, mode, metric)) for mode in MODES]
        cis = [bootstrap_ci(grouped(rows, depth, mode, metric)) for mode in MODES]
        errors = [[v-lo for v, (lo, hi) in zip(values, cis)], [hi-v for v, (lo, hi) in zip(values, cis)]]
        x = range(2)
        bars = ax.bar(x, values, yerr=errors, capsize=5,
                      color=[COLORS[m] for m in MODES], edgecolor='black', linewidth=0.8)
        for bar, mode in zip(bars, MODES):
            bar.set_hatch(HATCHES[mode])
        for i, mode in enumerate(MODES):
            observations = grouped(rows, depth, mode, metric)
            jitter = [i + (j-9.5)*0.006 for j in range(20)]
            ax.scatter(jitter, observations, s=14, color='black', alpha=0.45, zorder=3)
            ax.text(i, values[i], f'{values[i]:.2f}', ha='center', va='bottom', fontsize=9)
        ax.set_xticks([0, 1], [LABELS[m] for m in MODES])
        ax.set_ylabel(ylabel)
        ax.set_title(DEPTH_LABEL[depth])
        if zero:
            ax.set_ylim(bottom=0)
        style_axis(ax)
    fig.text(0.5, 0.045, 'Bars: mean; error bars: nonparametric bootstrap 95% CI; dots: individual simulation seeds (n=20).', ha='center', fontsize=8.5)
    add_footer(fig, page)
    pdf.savefig(fig)
    plt.close(fig)


def paired_metric_page(pdf, rows, page):
    fig, axes = plt.subplots(2, 2, figsize=(11.69, 8.27))
    fig.subplots_adjust(left=0.075, right=0.985, bottom=0.17, top=0.90, wspace=0.13, hspace=0.31)
    fig.suptitle('Reliability, Delay, and Timeout Comparison', fontsize=17, fontweight='bold')
    metrics = [('pdr_pct', 'Packet delivery ratio (%)'), ('packet_loss_pct', 'Packet loss ratio (%)'),
               ('average_rtt_ms', 'Average RTT (ms)'), ('timeout_ratio_pct', 'Timeout ratio (%)')]
    x = [0, 1, 3, 4]
    labels = ['Legacy\n15 m', 'Proposed\n15 m', 'Legacy\n1000 m', 'Proposed\n1000 m']
    combinations = [('depth15', 'legacy'), ('depth15', 'proposed'), ('depth1000', 'legacy'), ('depth1000', 'proposed')]
    for ax, (metric, ylabel) in zip(axes.flat, metrics):
        means = [statistics.mean(grouped(rows, d, m, metric)) for d, m in combinations]
        cis = [bootstrap_ci(grouped(rows, d, m, metric)) for d, m in combinations]
        errs = [[v-lo for v, (lo, hi) in zip(means, cis)], [hi-v for v, (lo, hi) in zip(means, cis)]]
        bars = ax.bar(x, means, yerr=errs, capsize=4,
                      color=[COLORS[m] for _, m in combinations], edgecolor='black', linewidth=0.8)
        for bar, (_, mode) in zip(bars, combinations):
            bar.set_hatch(HATCHES[mode])
        ax.set_xticks(x, labels)
        ax.set_ylabel(ylabel)
        ax.set_ylim(bottom=0)
        style_axis(ax)
    fig.text(0.5, 0.045, 'Mean across 20 seeds; error bars are bootstrap 95% confidence intervals.', ha='center', fontsize=8.5)
    add_footer(fig, page)
    pdf.savefig(fig)
    plt.close(fig)


def throughput_rtt_page(pdf, rows, page):
    fig, axes = plt.subplots(1, 2, figsize=(11.69, 8.27))
    fig.subplots_adjust(left=0.07, right=0.985, bottom=0.13, top=0.89, wspace=0.15)
    fig.suptitle('Throughput versus Average RTT', fontsize=17, fontweight='bold')
    markers = {'legacy': 's', 'proposed': '^'}
    for ax, depth in zip(axes, DEPTHS):
        for mode in MODES:
            subset = [r for r in rows if r['depth_case'] == depth and r['mode'] == mode]
            ax.scatter([r['average_rtt_ms'] for r in subset], [r['throughput_bps'] for r in subset],
                       label=LABELS[mode], color=COLORS[mode], marker=markers[mode], s=48,
                       edgecolor='black', linewidth=0.4, alpha=0.8)
        ax.set_xlabel('Average RTT (ms)')
        ax.set_ylabel('Throughput (bits/s)')
        ax.set_title(DEPTH_LABEL[depth])
        ax.set_xlim(left=0); ax.set_ylim(bottom=0)
        ax.grid(alpha=0.25)
        ax.spines[['top', 'right']].set_visible(False)
        ax.legend(frameon=False)
    add_footer(fig, page)
    pdf.savefig(fig)
    plt.close(fig)


def throughput_time_page(pdf, rows, page):
    fig, axes = plt.subplots(1, 2, figsize=(11.69, 8.27))
    fig.subplots_adjust(left=0.07, right=0.985, bottom=0.16, top=0.89, wspace=0.13)
    fig.suptitle('Throughput over Measurement Time', fontsize=17, fontweight='bold')
    markers = {'legacy': 's', 'proposed': '^'}
    for ax, depth in zip(axes, DEPTHS):
        for mode in MODES:
            subset = [r for r in rows if r['depth_case'] == depth and r['mode'] == mode]
            series = [time_binned_goodput(ROOT / r['run_dir'], 30) for r in subset]
            times = [p[0] for p in series[0]]
            means = [statistics.mean(run[i][1] for run in series) for i in range(len(times))]
            ax.plot(times, means, label=LABELS[mode], color=COLORS[mode], marker=markers[mode], linewidth=2)
        ax.set_xlabel('Measurement time (s)')
        ax.set_ylabel('Mean throughput (bits/s)')
        ax.set_title(DEPTH_LABEL[depth])
        ax.set_ylim(bottom=0)
        ax.grid(alpha=0.25)
        ax.spines[['top', 'right']].set_visible(False)
        ax.legend(frameon=False)
    fig.text(0.5, 0.045, 'Thirty-second bins; each point is the mean across the same 20 held-out seeds.', ha='center', fontsize=8.5)
    add_footer(fig, page)
    pdf.savefig(fig)
    plt.close(fig)


def adaptive_behavior_page(pdf, page):
    fig, axes = plt.subplots(2, 2, figsize=(11.69, 8.27))
    fig.subplots_adjust(left=0.075, right=0.985, bottom=0.17, top=0.90, wspace=0.16, hspace=0.31)
    fig.suptitle('Proposed Adaptive Controller: Logged Window Behaviour', fontsize=17, fontweight='bold')
    for col, depth in enumerate(DEPTHS):
        source = ROOT / 'results' / 'summary' / f'proposed_windows_{depth}.csv'
        with source.open(newline='', encoding='utf-8') as stream:
            rows = list(csv.DictReader(stream))
        obs = [int(r['observation']) for r in rows]
        interval = [float(r['next_interval_ms']) for r in rows]
        score = [float(r['weighted_score']) for r in rows]
        axes[0, col].plot(obs, interval, marker='o', color=COLORS['proposed'], linewidth=2)
        axes[0, col].set(title=DEPTH_LABEL[depth], xlabel='Resolved-window observation', ylabel='Next interval (ms)', ylim=(1000, 10000))
        axes[1, col].plot(obs, score, marker='o', color=COLORS['proposed'], linewidth=2)
        axes[1, col].axhline(0.15, color='#0072B2', linestyle='--', label='Healthy threshold')
        axes[1, col].axhline(0.30, color='#D55E00', linestyle=':', label='Poor threshold')
        axes[1, col].set(xlabel='Resolved-window observation', ylabel='Weighted score', ylim=(0, 1))
        axes[1, col].legend(frameon=False, fontsize=8)
        for ax in (axes[0, col], axes[1, col]):
            ax.set_xticks(obs); ax.grid(alpha=0.25); ax.spines[['top', 'right']].set_visible(False)
    fig.text(0.5, 0.045, 'These traces demonstrate controller logging from the earlier implementation; they are not final v2 controller evidence.', ha='center', fontsize=8.5)
    add_footer(fig, page)
    pdf.savefig(fig)
    plt.close(fig)


def title_page(pdf, rows):
    fig = plt.figure(figsize=(11.69, 8.27))
    fig.text(0.5, 0.84, 'Adaptive Data Rate Control for\nUnderwater Acoustic Networks', ha='center', fontsize=25, fontweight='bold')
    fig.text(0.5, 0.70, 'TA Progress Graphs: Legacy vs Proposed Adaptive', ha='center', fontsize=18, color='#333333')
    fig.text(0.5, 0.62, 'Team 9 - CS301 Mini Project', ha='center', fontsize=13)
    summary=[]
    for depth in DEPTHS:
        legacy=statistics.mean(grouped(rows,depth,'legacy','throughput_bps'))
        proposed=statistics.mean(grouped(rows,depth,'proposed','throughput_bps'))
        summary.append((DEPTH_LABEL[depth].split(': ')[1],legacy,proposed,100*(proposed-legacy)/legacy))
    ax=fig.add_axes([0.18,0.28,0.64,0.25]);ax.axis('off')
    table=ax.table(cellText=[[d,f'{l:.2f}',f'{p:.2f}',f'{g:+.1f}%'] for d,l,p,g in summary],
                   colLabels=['Depth','Legacy throughput','Proposed throughput','Relative change'],
                   cellLoc='center',loc='center')
    table.auto_set_font_size(False);table.set_fontsize(10);table.scale(1,1.7)
    fig.text(0.5, 0.18, 'Evidence source: earlier held-out evaluation, seeds 11-30 (n=20 paired runs per depth).', ha='center', fontsize=10)
    fig.text(0.5, 0.13, 'Important: these graphs compare legacy and proposed adaptive modes only. They are not the unfinished v2 5% result.', ha='center', fontsize=10, color='#A33A2B')
    add_footer(fig, 1)
    pdf.savefig(fig)
    plt.close(fig)


def progress_summary_page(pdf, rows, page):
    fig = plt.figure(figsize=(11.69, 8.27))
    fig.text(0.06, 0.91, 'Progress Completed and Current Finding', fontsize=20, fontweight='bold')

    completed = [
        'Implemented both legacy and proposed adaptive controllers in UnetStack 7.0.0.',
        'Ran a controlled held-out comparison using the same scenario and paired seeds.',
        'Completed 80 evaluation runs: 2 modes x 2 receiver depths x 20 seeds.',
        'Exported packet-level logs and computed delivery, ACK, RTT, timeout, interval, and throughput metrics.',
        'Generated reproducible analysis plots and bootstrap 95% confidence intervals.'
    ]
    fig.text(0.07, 0.84, 'Completed work', fontsize=14, fontweight='bold', color='#1B5E20')
    for index, item in enumerate(completed):
        fig.text(0.08, 0.79 - index * 0.048, f'{index + 1}. {item}', fontsize=10.5)

    table_rows = []
    for depth in DEPTHS:
        legacy = statistics.mean(grouped(rows, depth, 'legacy', 'throughput_bps'))
        proposed = statistics.mean(grouped(rows, depth, 'proposed', 'throughput_bps'))
        pdr_delta = (statistics.mean(grouped(rows, depth, 'proposed', 'pdr_pct')) -
                     statistics.mean(grouped(rows, depth, 'legacy', 'pdr_pct')))
        timeout_delta = (statistics.mean(grouped(rows, depth, 'proposed', 'timeout_ratio_pct')) -
                         statistics.mean(grouped(rows, depth, 'legacy', 'timeout_ratio_pct')))
        table_rows.append([
            DEPTH_LABEL[depth].split(': ')[1], f'{legacy:.2f}', f'{proposed:.2f}',
            f'{100 * (proposed - legacy) / legacy:+.1f}%', f'{pdr_delta:+.1f} pp', f'{timeout_delta:+.1f} pp'
        ])
    ax = fig.add_axes([0.06, 0.35, 0.88, 0.20])
    ax.axis('off')
    table = ax.table(
        cellText=table_rows,
        colLabels=['Depth', 'Legacy throughput', 'Proposed throughput', 'Throughput change', 'PDR change', 'Timeout change'],
        cellLoc='center', loc='center'
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9.5)
    table.scale(1, 1.8)
    for column in range(6):
        table[(0, column)].set_facecolor('#DCEFE8')
        table[(0, column)].set_text_props(fontweight='bold')

    fig.text(0.07, 0.27, 'TA-ready conclusion', fontsize=14, fontweight='bold', color='#0B5D75')
    conclusion = (
        'The proposed controller approximately doubled useful throughput at both depths. '
        'However, it did so by sending much more aggressively: delivery ratio and ACK ratio fell, while RTT and timeout ratio rose. '
        'Therefore, the current result demonstrates successful implementation and a clear throughput gain, but also identifies '
        'feedback reliability as the next engineering problem to solve.'
    )
    fig.text(0.07, 0.22, conclusion, fontsize=10.5, wrap=True, va='top')
    fig.text(0.07, 0.10, 'Status: implementation and held-out validation complete; reliability-focused refinement remains.',
             fontsize=11, fontweight='bold')
    add_footer(fig, page)
    pdf.savefig(fig)
    plt.close(fig)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--force',action='store_true')
    args=parser.parse_args()
    rows=read_rows()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    if OUTPUT.exists():
        if not args.force:
            raise FileExistsError(f'Refusing to overwrite {OUTPUT}')
        OUTPUT.unlink()
    with PdfPages(OUTPUT, metadata={'Title':'TA Progress - Legacy vs Proposed Adaptive',
                                    'Author':'Team 9',
                                    'Subject':'Interim UnetStack held-out evaluation graphs'}) as pdf:
        title_page(pdf, rows)
        progress_summary_page(pdf, rows, 2)
        bar_page(pdf, rows, 'throughput_bps', 'Throughput (bits/s)', 'Throughput Comparison', 3)
        paired_metric_page(pdf, rows, 4)
        throughput_rtt_page(pdf, rows, 5)
        throughput_time_page(pdf, rows, 6)
        adaptive_behavior_page(pdf, 7)
    print(json.dumps({'output':str(OUTPUT),'pages':7,'source':str(SOURCE),'runs':len(rows)},indent=2))


if __name__ == '__main__':
    main()
