from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf" / "TA_Progress_Report_Protocol_v3.pdf"
FIGURES = ROOT / "results" / "v3" / "figures"

BLUE = colors.HexColor("#0B4F6C")
GREEN = colors.HexColor("#0B8F6A")
LIGHT = colors.HexColor("#EAF4F4")
GRAY = colors.HexColor("#4B5563")


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#D1D5DB"))
    canvas.line(18 * mm, 13 * mm, 192 * mm, 13 * mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GRAY)
    canvas.drawString(18 * mm, 8 * mm, "CN Mini Project - UnetStack 7.0.0 - Protocol v3")
    canvas.drawRightString(192 * mm, 8 * mm, f"Page {doc.page}")
    canvas.restoreState()


styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name="TitleCustom", parent=styles["Title"], fontName="Helvetica-Bold",
    fontSize=23, leading=28, textColor=BLUE, alignment=TA_CENTER, spaceAfter=10,
))
styles.add(ParagraphStyle(
    name="Subtitle", parent=styles["Normal"], fontSize=11, leading=15,
    textColor=GRAY, alignment=TA_CENTER, spaceAfter=16,
))
styles.add(ParagraphStyle(
    name="H1Custom", parent=styles["Heading1"], fontName="Helvetica-Bold",
    fontSize=16, leading=20, textColor=BLUE, spaceBefore=8, spaceAfter=8,
))
styles.add(ParagraphStyle(
    name="H2Custom", parent=styles["Heading2"], fontName="Helvetica-Bold",
    fontSize=12, leading=15, textColor=GREEN, spaceBefore=7, spaceAfter=5,
))
styles.add(ParagraphStyle(
    name="BodyCustom", parent=styles["BodyText"], fontSize=9.5, leading=14,
    textColor=colors.HexColor("#1F2937"), spaceAfter=6,
))
styles.add(ParagraphStyle(
    name="Small", parent=styles["BodyText"], fontSize=8, leading=11,
    textColor=GRAY, spaceAfter=4,
))
styles.add(ParagraphStyle(
    name="Callout", parent=styles["BodyText"], fontName="Helvetica-Bold",
    fontSize=11, leading=16, textColor=colors.white, backColor=GREEN,
    borderPadding=9, spaceBefore=8, spaceAfter=10,
))


def p(text, style="BodyCustom"):
    return Paragraph(text, styles[style])


def table(data, widths, header=True, font=8):
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold" if header else "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), font),
        ("LEADING", (0, 0), (-1, -1), font + 3),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9CA3AF")),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if header:
        commands += [
            ("BACKGROUND", (0, 0), (-1, 0), BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ]
    t.setStyle(TableStyle(commands))
    return t


def build():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUTPUT), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm,
        topMargin=17 * mm, bottomMargin=18 * mm, title="TA Progress Report - Protocol v3",
        author="CN Mini Project Team",
    )
    story = []
    story += [
        Spacer(1, 8 * mm),
        p("Adaptive Data Rate Control for Underwater Acoustic Networks", "TitleCustom"),
        p("TA Progress Report - Protocol Version 3 - 30 October 2026", "Subtitle"),
        table([
            ["Roll No.", "Team member"],
            ["241CS132", "M. Dhakshesh Naidu"],
            ["241CS142", "Pratham M. Attavar"],
            ["241CS158", "Srikara Nikhil"],
        ], [38 * mm, 115 * mm], font=9),
        Spacer(1, 8 * mm),
        p("Outcome", "H1Custom"),
        p("The proposed application-layer method exceeded the fixed 3000 ms baseline at both tested depths. It combines sparse ACK sampling, receiver-validated feedback, adaptive pacing, and bounded selective retransmission. The modem, MAC, topology, payload, and channel probabilities remain unchanged."),
        p("Held-out result: throughput improved by 30.63% at 15 m and 24.30% at 1000 m; PDR improved by 22.48 and 19.26 percentage points. All paired 95% bootstrap intervals exclude zero.", "Callout"),
        p("What changed", "H1Custom"),
        table([
            ["Parameter", "Fixed baseline", "Proposed v3", "Reason"],
            ["ACK policy", "Every original", "2 per 10 originals + retries", "Reduce reverse-channel traffic"],
            ["Recovery", "No retry", "Missing IDs only", "Recover confirmed loss"],
            ["Retry cadence", "None", "1 after 4 new originals", "Bound recovery load"],
            ["Retry cap", "None", "3 per original window", "Prevent retry explosion"],
            ["Retry identity", "N/A", "At most attempt 2", "One retry per useful ID"],
            ["Weights", "N/A", "[0.15, 0.55, 0.15, 0.15]", "Prioritize confirmed loss"],
        ], [27 * mm, 30 * mm, 46 * mm, 54 * mm], font=7.4),
        Spacer(1, 4 * mm),
        p("The weights correspond to RTT, confirmed loss, ACK failure, and timeout. The sending interval is latched for each ten-original window so a late controller decision cannot change pacing halfway through a window.", "Small"),
        PageBreak(),
        p("Algorithm", "H1Custom"),
        p("1. Node A creates a stable sequence ID and sends a 64-byte original DATA frame. Proposed mode requests ACKs only for the last original sent to each receiver in a ten-message window."),
        p("2. Each receiver records unique sequence IDs. Its first final snapshot for a receiver/window is frozen and returned by a sampled ACK or report."),
        p("3. The sender compares expected IDs with the snapshot. Missing IDs enter a deterministic retry queue. A sequence can be retried once, a window can create at most three retries, and one retry opportunity follows four new originals."),
        p("4. Original and retry DATA share one paced scheduler. A retry uses an opportunity instead of creating a parallel traffic stream."),
        p("5. Final metrics count unique original IDs. Retries, duplicates, and ACKs never enlarge the useful-message denominator."),
        p("Experiment design", "H1Custom"),
        table([
            ["Item", "Value"],
            ["Simulator", "UnetStack 7.0.0, ProtocolChannelModel"],
            ["Topology", "A, B, C at horizontal positions 0, 1, 2 km"],
            ["Depth cases", "C at 15 m and 1000 m; A and B at 15 m"],
            ["Payload", "64 bytes (512 useful bits)"],
            ["Warm-up / measurement", "60 s / 180 s"],
            ["Screening", "Seeds 181-185; 280 units"],
            ["Calibration", "Seeds 201-210; 112 units"],
            ["Held-out evaluation", "Seeds 211-230; 80 units"],
        ], [50 * mm, 105 * mm], font=8),
        Spacer(1, 6 * mm),
        p("Reproducibility and fairness", "H2Custom"),
        p("Fixed and proposed modes use identical paired seeds, topology, duration, payload, and channel conditions. The frozen configuration was written before any held-out evaluation seed ran. Manifests include protocol, ACK policy, retry cadence/cap, controller settings, seed, and duration."),
        p("Metric definitions", "H2Custom"),
        p("PDR = unique delivered / unique generated. Useful throughput = unique delivered x 512 / 180 s. Retry overhead = retry DATA attempts / all DATA attempts. Late unique retry delivery counts once; duplicate delivery counts zero additional useful messages."),
        PageBreak(),
        p("Held-out results", "H1Custom"),
        table([
            ["Depth", "Mode", "Generated", "Attempts", "Delivered", "PDR", "Throughput", "Retry OH"],
            ["15 m", "Fixed", "60.00", "60.00", "36.05", "60.08%", "102.54 bit/s", "0.00%"],
            ["15 m", "Proposed", "56.75", "60.00", "46.85", "82.57%", "133.26 bit/s", "5.42%"],
            ["1000 m", "Fixed", "60.00", "60.00", "37.45", "62.42%", "106.52 bit/s", "0.00%"],
            ["1000 m", "Proposed", "56.90", "60.00", "46.45", "81.68%", "132.12 bit/s", "5.17%"],
        ], [18 * mm, 24 * mm, 21 * mm, 20 * mm, 22 * mm, 20 * mm, 29 * mm, 20 * mm], font=7.2),
        Spacer(1, 5 * mm),
        table([
            ["Depth", "Throughput gain (95% CI)", "PDR gain (95% CI)", "Formal gate"],
            ["15 m", "+30.63% (+25.71 to +35.44)", "+22.48 pp (+20.66 to +24.35)", "PASS"],
            ["1000 m", "+24.30% (+21.00 to +27.58)", "+19.26 pp (+17.54 to +21.01)", "PASS"],
        ], [23 * mm, 54 * mm, 54 * mm, 25 * mm], font=8),
        Spacer(1, 6 * mm),
        Image(str(FIGURES / "throughput_comparison.png"), width=170 * mm, height=76.5 * mm),
        p("Figure 1. Mean useful throughput with bootstrap uncertainty across 20 held-out paired seeds per depth.", "Small"),
        PageBreak(),
        p("Reliability result", "H1Custom"),
        Image(str(FIGURES / "packet_delivery.png"), width=170 * mm, height=76.5 * mm),
        p("Figure 2. Mean packet delivery ratio with bootstrap uncertainty. Proposed mode increases reliability at both depths.", "Small"),
        p("Depth interpretation", "H1Custom"),
        p("The statement 'throughput generally increases with depth' is not supported. For fixed mode, the paired 1000 m minus 15 m effect was +3.98 bit/s with a 95% CI of +0.57 to +7.82. For proposed mode it was -1.14 bit/s with a CI of -3.56 to +1.42, which is inconclusive."),
        p("Depth changes 3D distance, propagation timing, and collision alignment in this model. It does not directly improve detection or decoding probability, because those probabilities are configured independently of depth."),
        p("One-line viva answer", "H1Custom"),
        p("We reduced reverse ACK load and used bounded receiver-confirmed retries; this raised unique-message throughput by at least 24.30% and PDR by at least 19.26 points in held-out paired tests, with only about 5% retry overhead.", "Callout"),
        p("Limitations", "H2Custom"),
        p("These are simulation results for the declared topology and moderate channel model. The simulator does not model thermoclines, salinity profiles, pressure effects, or a depth-dependent sound-speed profile. The measured gain should not be generalized beyond the evaluated conditions without new experiments."),
        PageBreak(),
        p("Reproduce and verify", "H1Custom"),
        p("Run from the UnetStack project root on a lab machine with a compatible Java installation:"),
        p("python analysis/run_experiments.py evaluation --config results/v3/calibration/frozen-config.json --workers 8 --measurement 180", "Small"),
        p("python analysis/analyze_results.py --runs results/v3/runs/evaluation --output results/v3", "Small"),
        p("Key evidence", "H1Custom"),
        table([
            ["Artifact", "Repository path"],
            ["Frozen parameters", "results/v3/calibration/frozen-config.json"],
            ["Per-run metrics", "results/v3/summary/run_summary.csv"],
            ["Paired effects", "results/v3/summary/paired_effects.csv"],
            ["Depth effects", "results/v3/summary/depth_effects.csv"],
            ["Success gates", "results/v3/summary/success.json"],
            ["Raw evaluation", "results/v3/runs/evaluation/"],
        ], [50 * mm, 105 * mm], font=8),
        Spacer(1, 8 * mm),
        p("Final conclusion", "H1Custom"),
        p("Protocol version 3 meets the project target against the fixed 3000 ms baseline at both depths. The improvement is an application-layer contribution: ACK thinning plus bounded selective repeat integrated with receiver-validated adaptive pacing. Legacy mode is not the official baseline."),
        p("Prepared from the validated version-3 held-out results. No result was manually altered or relabeled.", "Small"),
    ]
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(OUTPUT)


if __name__ == "__main__":
    build()
