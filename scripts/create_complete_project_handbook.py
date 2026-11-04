from __future__ import annotations

import csv
import html
from pathlib import Path

from PIL import Image as PILImage
from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import (
    Flowable,
    Image,
    KeepTogether,
    LongTable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf" / "Complete_Project_and_Lab_Handbook_Protocol_v3.pdf"
SUMMARY = ROOT / "results" / "v3" / "summary"
MATLAB_FIGURES = ROOT / "results" / "v3" / "matlab_figures"
PYTHON_FIGURES = ROOT / "results" / "v3" / "figures"

NAVY = colors.HexColor("#12324A")
BLUE = colors.HexColor("#0072B2")
ORANGE = colors.HexColor("#D55E00")
GREEN = colors.HexColor("#007A5E")
INK = colors.HexColor("#17212B")
MUTED = colors.HexColor("#556270")
PALE_BLUE = colors.HexColor("#EAF3F8")
PALE_ORANGE = colors.HexColor("#FCEFE7")
PALE_GREEN = colors.HexColor("#E8F5EF")
LINE = colors.HexColor("#AAB7C4")


def read_csv(name: str) -> list[dict[str, str]]:
    with (SUMMARY / name).open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


overall = read_csv("overall_comparison.csv")
paired = read_csv("paired_effects.csv")
depth_effects = read_csv("depth_effects.csv")


def find(rows: list[dict[str, str]], **match: str) -> dict[str, str]:
    selected = [row for row in rows if all(row[key] == value for key, value in match.items())]
    if len(selected) != 1:
        raise ValueError(f"Expected one row for {match}, found {len(selected)}")
    return selected[0]


fixed15 = find(overall, depth_case="depth15", approach="fixed")
proposed15 = find(overall, depth_case="depth15", approach="proposed")
fixed1000 = find(overall, depth_case="depth1000", approach="fixed")
proposed1000 = find(overall, depth_case="depth1000", approach="proposed")
effect15 = find(paired, depth_case="depth15")
effect1000 = find(paired, depth_case="depth1000")
depth_fixed = find(depth_effects, mode="fixed")
depth_proposed = find(depth_effects, mode="proposed")


try:
    pdfmetrics.registerFont(TTFont("DejaVuSans", "C:/Windows/Fonts/DejaVuSans.ttf"))
    pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", "C:/Windows/Fonts/DejaVuSans-Bold.ttf"))
    BODY_FONT = "DejaVuSans"
    BOLD_FONT = "DejaVuSans-Bold"
except Exception:
    BODY_FONT = "Helvetica"
    BOLD_FONT = "Helvetica-Bold"


styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name="CoverTitle", parent=styles["Title"], fontName=BOLD_FONT,
    fontSize=25, leading=31, textColor=NAVY, alignment=TA_CENTER, spaceAfter=8,
))
styles.add(ParagraphStyle(
    name="CoverSub", parent=styles["Normal"], fontName=BODY_FONT,
    fontSize=12, leading=17, textColor=MUTED, alignment=TA_CENTER, spaceAfter=12,
))
styles.add(ParagraphStyle(
    name="H1x", parent=styles["Heading1"], fontName=BOLD_FONT,
    fontSize=17, leading=21, textColor=NAVY, spaceBefore=5, spaceAfter=8,
))
styles.add(ParagraphStyle(
    name="H2x", parent=styles["Heading2"], fontName=BOLD_FONT,
    fontSize=12.5, leading=16, textColor=BLUE, spaceBefore=7, spaceAfter=5,
))
styles.add(ParagraphStyle(
    name="H3x", parent=styles["Heading3"], fontName=BOLD_FONT,
    fontSize=10.5, leading=13, textColor=GREEN, spaceBefore=5, spaceAfter=3,
))
styles.add(ParagraphStyle(
    name="Bodyx", parent=styles["BodyText"], fontName=BODY_FONT,
    fontSize=9.2, leading=13.4, textColor=INK, alignment=TA_JUSTIFY, spaceAfter=5,
))
styles.add(ParagraphStyle(
    name="Smallx", parent=styles["BodyText"], fontName=BODY_FONT,
    fontSize=7.5, leading=10.3, textColor=MUTED, spaceAfter=3,
))
styles.add(ParagraphStyle(
    name="Captionx", parent=styles["BodyText"], fontName=BODY_FONT,
    fontSize=7.6, leading=10.2, textColor=MUTED, alignment=TA_LEFT, spaceAfter=6,
))
styles.add(ParagraphStyle(
    name="Calloutx", parent=styles["BodyText"], fontName=BOLD_FONT,
    fontSize=10.5, leading=15, textColor=colors.white, backColor=GREEN,
    borderPadding=9, spaceBefore=6, spaceAfter=9,
))
styles.add(ParagraphStyle(
    name="Warningx", parent=styles["BodyText"], fontName=BOLD_FONT,
    fontSize=9.2, leading=13, textColor=INK, backColor=PALE_ORANGE,
    borderColor=ORANGE, borderWidth=0.8, borderPadding=7, spaceBefore=5, spaceAfter=7,
))
styles.add(ParagraphStyle(
    name="Bulletx", parent=styles["BodyText"], fontName=BODY_FONT,
    fontSize=9, leading=12.5, leftIndent=12, firstLineIndent=-7,
    bulletIndent=3, textColor=INK, spaceAfter=3,
))
styles.add(ParagraphStyle(
    name="Codex", parent=styles["Code"], fontName="Courier",
    fontSize=6.8, leading=8.4, leftIndent=5, rightIndent=5,
    textColor=colors.HexColor("#082F49"), spaceAfter=0.5,
))
styles.add(ParagraphStyle(
    name="TableHead", parent=styles["Normal"], fontName=BOLD_FONT,
    fontSize=7.3, leading=9.3, textColor=colors.white,
))
styles.add(ParagraphStyle(
    name="TableCell", parent=styles["Normal"], fontName=BODY_FONT,
    fontSize=7.2, leading=9.4, textColor=INK,
))
styles.add(ParagraphStyle(
    name="TableCellBold", parent=styles["Normal"], fontName=BOLD_FONT,
    fontSize=7.2, leading=9.4, textColor=INK,
))


class HorizontalRule(Flowable):
    def __init__(self, width: float, color=LINE, thickness=0.7):
        super().__init__()
        self.width = width
        self.color = color
        self.thickness = thickness
        self.height = 4

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 2, self.width, 2)


def safe(value: object) -> str:
    return html.escape(str(value), quote=False)


def p(text: str, style: str = "Bodyx") -> Paragraph:
    return Paragraph(text, styles[style])


def bullet(text: str) -> Paragraph:
    return Paragraph(safe(text), styles["Bulletx"], bulletText="-")


def heading(text: str, level: int = 1) -> Paragraph:
    return p(safe(text), {1: "H1x", 2: "H2x", 3: "H3x"}[level])


def cell(value: object, header: bool = False, bold: bool = False) -> Paragraph:
    style = "TableHead" if header else ("TableCellBold" if bold else "TableCell")
    return Paragraph(safe(value), styles[style])


def make_table(
    rows: list[list[object]], widths: list[float], *, repeat: bool = True,
    header: bool = True, bold_first: bool = False, font_size: float | None = None,
) -> LongTable:
    converted = []
    for r_index, row in enumerate(rows):
        converted.append([
            cell(value, header=header and r_index == 0, bold=bold_first and c_index == 0)
            for c_index, value in enumerate(row)
        ])
    table = LongTable(converted, colWidths=widths, repeatRows=1 if repeat and header else 0, hAlign="LEFT")
    commands = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.35, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if header:
        commands.extend([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE_BLUE]),
        ])
    else:
        commands.append(("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, PALE_BLUE]))
    if font_size:
        commands.extend([
            ("FONTSIZE", (0, 0), (-1, -1), font_size),
            ("LEADING", (0, 0), (-1, -1), font_size + 2),
        ])
    table.setStyle(TableStyle(commands))
    return table


def code_block(code: str) -> list[Paragraph]:
    result = []
    for line in code.rstrip().splitlines():
        visible = safe(line).replace(" ", "&nbsp;") or "&nbsp;"
        result.append(Paragraph(visible, styles["Codex"]))
    return result


def add_figure(story: list, path: Path, caption: str, max_height_mm: float = 102) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)
    with PILImage.open(path) as image:
        width_px, height_px = image.size
    max_width = 174 * mm
    max_height = max_height_mm * mm
    scale = min(max_width / width_px, max_height / height_px)
    story.append(Image(str(path), width=width_px * scale, height=height_px * scale, hAlign="CENTER"))
    story.append(p(safe(caption), "Captionx"))


def page_header_footer(canvas, doc):
    canvas.saveState()
    page = canvas.getPageNumber()
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.5)
    canvas.line(18 * mm, 284 * mm, 192 * mm, 284 * mm)
    canvas.setFont(BOLD_FONT, 7.2)
    canvas.setFillColor(NAVY)
    canvas.drawString(18 * mm, 287 * mm, "Adaptive Data Rate Control - Complete Project and Lab Handbook")
    canvas.setFont(BODY_FONT, 7.2)
    canvas.setFillColor(MUTED)
    canvas.line(18 * mm, 13 * mm, 192 * mm, 13 * mm)
    canvas.drawString(18 * mm, 8 * mm, "UnetStack 7.0.0 | Protocol v3 | Validated held-out evaluation")
    canvas.drawRightString(192 * mm, 8 * mm, f"Page {page}")
    canvas.restoreState()


def fmt(row: dict[str, str], key: str, digits: int = 2) -> str:
    return f"{float(row[key]):.{digits}f}"


def build_story() -> list:
    story: list = []

    story.extend([
        Spacer(1, 16 * mm),
        p("Adaptive Data Rate Control for Underwater Acoustic Networks", "CoverTitle"),
        p("Complete Project Explanation, Final Results, Implementation Guide, MATLAB Workflow, and TA Viva Notes", "CoverSub"),
        Spacer(1, 5 * mm),
        make_table([
            ["Roll No.", "Team member"],
            ["241CS132", "M. Dhakshesh Naidu"],
            ["241CS142", "Pratham M. Attavar"],
            ["241CS158", "Srikara Nikhil"],
        ], [38 * mm, 120 * mm]),
        Spacer(1, 8 * mm),
        p("Final verified outcome", "H1x"),
        p(
            f"Compared with the fixed 3000 ms baseline, proposed protocol v3 improved useful throughput by "
            f"<b>{fmt(effect15, 'throughput_change_pct')}%</b> at 15 m and "
            f"<b>{fmt(effect1000, 'throughput_change_pct')}%</b> at 1000 m. Packet-delivery ratio improved by "
            f"<b>{fmt(effect15, 'pdr_change_pp')} percentage points</b> and "
            f"<b>{fmt(effect1000, 'pdr_change_pp')} percentage points</b>. All four paired 95% bootstrap "
            f"confidence intervals exclude zero.",
            "Calloutx",
        ),
        p(
            "Evidence boundary: these are controlled UnetStack simulation results for the declared topology, "
            "moderate protocol channel, and paired seeds. They are not a claim that the same numerical gain is "
            "guaranteed in every ocean deployment.",
            "Warningx",
        ),
        Spacer(1, 4 * mm),
        p("Prepared 31 October 2026 | Protocol version 3 | UnetStack 7.0.0 | MATLAB R2026b workflow verified", "Smallx"),
        PageBreak(),
    ])

    story.extend([
        heading("How to use this handbook"),
        p("Use Sections 1-5 to learn the project, Sections 6-8 to explain the evidence, and Sections 9-12 while performing the lab demonstration. The appendices give the code map, complete MATLAB source, exact artifacts, and quick viva answers."),
        heading("Contents", 2),
        make_table([
            ["Part", "What it contains"],
            ["1. Problem", "Why fixed-rate underwater traffic control is inefficient"],
            ["2. Our idea", "ACK thinning, receiver-validated feedback, adaptive pacing, bounded selective retry"],
            ["3. Method", "Message flow, weights, windows, scheduler, and depth treatment"],
            ["4. Technical terms", "Definitions needed for a TA explanation"],
            ["5. Experiment", "Topology, metrics, fairness, seeds, and statistical method"],
            ["6-8. Results", "Exact tables, confidence intervals, all main graphs, and depth conclusion"],
            ["9-10. Implementation", "Source files, environment variables, and UnetStack commands"],
            ["11. MATLAB", "How CSV becomes figures and the complete MATLAB code"],
            ["12-14. Demo and viva", "What to show, what to say, limitations, future work, references"],
        ], [36 * mm, 124 * mm]),
        heading("The 30-second explanation", 2),
        p("The fixed baseline sends one 64-byte application message every 3000 ms, requests an ACK for every original, and performs no application retry. Proposed v3 requests only two original ACKs in every ten-message window, uses the receiver's immutable delivery snapshot to identify truly missing sequence IDs, and gives a bounded retry opportunity after four new originals. Unique IDs - not attempts - define throughput and reliability, so retries cannot inflate the result."),
        PageBreak(),
    ])

    story.extend([
        heading("1. What problem is this project solving?"),
        p("Underwater nodes commonly communicate acoustically. Compared with terrestrial radio, acoustic networking has much longer propagation delays, restricted bandwidth, half-duplex operation, and time-varying loss. These properties make traffic timing important at the network and application levels."),
        heading("Why a fixed interval is a problem", 2),
        bullet("If the sender injects packets too frequently, transmissions and acknowledgements can overlap, queues can grow, and more deadlines can expire."),
        bullet("If the sender injects packets too slowly, the channel can be idle and useful throughput falls."),
        bullet("A fixed 3000 ms interval cannot use measured RTT, receiver delivery evidence, ACK behavior, or timeout history to respond to observed conditions."),
        heading("Precise project question", 2),
        p("Under the same UnetStack topology, channel, duration, payload, and random seed, can a receiver-validated application-layer protocol deliver more unique payload bits and a higher fraction of unique messages than fixed 3000 ms transmission?"),
        heading("Why this is a Computer Networks project", 2),
        p("The contribution is application-layer traffic control and feedback behavior. The project does not change acoustic modulation, coding, transmit power, the modem model, or the CSMA implementation. UnetStack remains central for network simulation; MATLAB is used to reproduce the final presentation figures from validated CSV summaries."),
        heading("Baseline, legacy, and proposed are different", 2),
        make_table([
            ["Mode", "Meaning", "Role in final claim"],
            ["Fixed", "Always uses a 3000 ms sending interval; ACK every original; no application retry.", "Official baseline"],
            ["Legacy adaptive", "Older event-driven controller that changes interval after individual ACKs and timeouts.", "Historical code path; not the official held-out baseline"],
            ["Proposed v3", "Windowed receiver feedback, sparse ACKs, adaptive candidate interval, and bounded selective retransmission.", "Our improved solution"],
        ], [30 * mm, 86 * mm, 48 * mm]),
        p("Do not call legacy the fixed baseline. Fixed is non-adaptive; legacy is an older adaptive method." , "Warningx"),
        PageBreak(),
    ])

    story.extend([
        heading("2. Our idea and specific contribution"),
        heading("Core idea", 2),
        p("Instead of reacting to every ACK, proposed v3 evaluates traffic in ten-original windows. It reduces reverse-channel ACK load, obtains receiver-validated delivery information, schedules only a few selective retries, and uses a weighted network-condition score to choose among safe candidate intervals."),
        make_table([
            ["Mechanism", "Fixed baseline", "Proposed v3", "Why it helps"],
            ["Original ACK policy", "Every original", "Last two originals per ten-message window", "Reduces reverse traffic"],
            ["Delivery evidence", "ACK presence", "Immutable receiver snapshot", "Separates missing data from missing ACK"],
            ["Recovery", "None", "Retry confirmed missing IDs", "Recovers useful messages"],
            ["Retry cadence", "None", "One eligible retry after four new originals", "Prevents recovery burst"],
            ["Retry cap", "None", "At most three per source window", "Bounds overhead"],
            ["Sequence attempts", "One", "At most two", "Prevents retry explosion"],
            ["Pacing", "3000 ms", "Candidate interval latched for a full window", "Avoids mid-window instability"],
        ], [27 * mm, 31 * mm, 49 * mm, 57 * mm]),
        heading("What is actually new over the baseline", 2),
        bullet("Sparse original acknowledgements instead of one ACK for every original."),
        bullet("Receiver-confirmed missing-ID recovery rather than treating every ACK timeout as packet loss."),
        bullet("A single paced opportunity stream shared by new originals and retries."),
        bullet("Deterministic retry cadence and hard per-window/per-ID bounds."),
        bullet("Unique-message accounting so duplicate attempts cannot manufacture throughput."),
        heading("One-line reason for every frozen parameter", 2),
        make_table([
            ["Parameter", "Frozen value", "One-line reason"],
            ["RTT weight", "0.15", "Delay matters, but sampled ACKs make it secondary to delivery evidence."],
            ["Confirmed-loss weight", "0.55", "Receiver snapshots directly identify missing unique IDs, so loss gets the highest influence."],
            ["ACK-failure weight", "0.15", "Missing ACKs still indicate feedback difficulty but do not prove DATA loss."],
            ["Timeout weight", "0.15", "Deadline expiry is a congestion/delay warning, not definitive delivery evidence."],
            ["Window size", "10 originals", "Provides enough observations while keeping decisions responsive."],
            ["Retry cadence", "After 4 new originals", "Recovery is interleaved with fresh traffic instead of bursting."],
            ["Retry cap", "3 per window", "Limits retry load to a small fraction of DATA opportunities."],
            ["Per-ID attempts", "Maximum 2", "Each useful message receives at most one recovery attempt."],
            ["Fixed interval", "3000 ms", "Preserves the required non-adaptive comparison."],
        ], [38 * mm, 32 * mm, 94 * mm]),
        PageBreak(),
    ])

    story.extend([
        heading("3. How the algorithm works"),
        heading("Message flow", 2),
    ])
    story.extend(code_block(
        "Node A (sender)                               Node B / Node C\n"
        "    |-- DATA(window, seq, attempt=1, ack?) ------->|\n"
        "    |                                             | record unique seq\n"
        "    |<-- sampled ACK + prior-window snapshot -----|\n"
        "    |-- DATA(same seq, attempt=2, ack=true) ------>|  only if snapshot says missing\n"
        "    |<-- retry ACK -------------------------------|"
    ))
    story.extend([
        Spacer(1, 3 * mm),
        heading("Step-by-step logic", 2),
        bullet("Create a stable sequence ID and choose B or C by alternating destinations."),
        bullet("Send a 64-byte DATA frame. In proposed mode, request an ACK only for the final two original positions in a ten-original window; every retry requests an ACK."),
        bullet("At the receiver, add the sequence ID to the unique delivery set. Duplicates do not create another useful delivery."),
        bullet("Freeze the first valid receiver snapshot for that receiver/window. Later events cannot rewrite the historical control observation."),
        bullet("Compare expected IDs with delivered IDs. Put only confirmed missing IDs in a deterministic retry queue."),
        bullet("After four new originals, allow one queued retry to consume the next paced opportunity. Never create a second traffic stream."),
        bullet("When a window is resolved, compute RTT, confirmed loss, ACK-failure, and timeout penalties and apply the four weights."),
        bullet("Choose the next interval from 2000, 2250, 2500, 2700, 3000, 3375, 3750, 4500, or 6000 ms, then latch it for the full next original window."),
        heading("What the weights mean", 2),
        p("A weight is the fraction of influence assigned to a normalized signal in the controller score. The four weights sum to one. For example, 0.55 on confirmed loss means that receiver-confirmed missing messages contribute more to a poor-condition score than any single other signal. A weight is not a probability and does not mean that 55% of packets are lost."),
        heading("Why unique IDs matter", 2),
        p("A retry keeps the same sequence ID and uses attempt 2. If attempt 1 and attempt 2 both arrive, the receiver still counts one useful message. This prevents duplicate transmissions from inflating PDR or useful throughput."),
        PageBreak(),
    ])

    glossary = [
        ("Application layer", "The layer containing this traffic-control logic; it decides when to create/send application DATA and how to use feedback."),
        ("Underwater acoustic network", "A network whose nodes exchange information through sound in water."),
        ("Node", "One simulated network device. A is the sender; B and C are receivers."),
        ("Packet / DATA frame", "A transmitted protocol unit. The application payload is 64 bytes in this experiment."),
        ("Payload", "Useful application data carried by a DATA transmission; ACK/report bytes are not useful payload."),
        ("Sequence ID", "Stable identifier of one unique application message; a retry uses the same ID."),
        ("Attempt", "One transmission of a sequence ID. Original is attempt 1; the single permitted retry is attempt 2."),
        ("Sending interval", "Time between paced DATA opportunities. Fixed mode uses 3000 ms."),
        ("Physical data rate", "Bit rate configured in the modem model (2400 bit/s here); it is different from the application sending interval."),
        ("Throughput", "Rate at which information is delivered. This report uses useful payload throughput, often called goodput."),
        ("Useful throughput / goodput", "Unique delivered payload bits divided by the fixed 180 s measurement time."),
        ("PDR", "Packet-delivery ratio: unique delivered messages divided by unique generated messages."),
        ("Confirmed packet loss", "Generated unique IDs absent from receiver delivery evidence; not merely missing ACKs."),
        ("ACK", "Acknowledgement sent by a receiver to confirm a DATA attempt and optionally carry a snapshot."),
        ("ACK thinning", "Requesting fewer original ACKs to reduce reverse-channel traffic."),
        ("RTT", "Round-trip time from sending a DATA attempt to receiving its matching ACK."),
        ("Timeout", "The ACK deadline expired. A timeout is not proof that the DATA packet was lost."),
        ("Late ACK", "An ACK that arrives after its deadline; it remains measurable without erasing the historical timeout."),
        ("Feedback window", "A group of ten originals used as one controller observation unit."),
        ("Receiver snapshot", "Immutable set of unique sequence IDs received for a completed window."),
        ("Selective retransmission", "Retry only IDs known missing instead of repeating every message."),
        ("Bounded retry", "Hard limits on retry frequency, retries per window, and attempts per ID."),
        ("Retry cadence", "Rule controlling when a queued retry may consume a paced opportunity."),
        ("Overhead", "Extra protocol work not counted as new useful payload, such as ACKs, reports, and retries."),
        ("Controller", "Algorithm mapping observed network metrics to a future sending interval."),
        ("Weighted score", "Sum of normalized penalties multiplied by their importance weights."),
        ("Penalty", "A normalized 0-to-1 indicator of undesirable network behavior."),
        ("Candidate interval", "One allowed interval from the frozen discrete list; prevents arbitrary unbounded changes."),
        ("Interval latch", "Keeps the selected interval constant throughout one complete original window."),
        ("Fixed baseline", "Required comparison that always sends at 3000 ms."),
        ("Legacy adaptive", "Older per-event RTT/timeout controller; adaptive, but not the official baseline."),
        ("Proposed v3", "Our ACK-thinned, receiver-validated, bounded-retry adaptive protocol."),
        ("Calibration", "Parameter selection using seeds reserved before final evaluation."),
        ("Held-out evaluation", "Final runs not used to choose the frozen parameters."),
        ("Random seed", "Value making stochastic simulation conditions reproducible and pairable."),
        ("Paired comparison", "Fixed and proposed use the same seed and conditions so their difference is less confounded by random variation."),
        ("Independent replicate", "One complete seeded run; individual packets in the same run are not independent experiments."),
        ("Bootstrap 95% CI", "Interval obtained by resampling paired run-level effects; it summarizes uncertainty in the mean paired effect."),
        ("Warm-up", "Initial 60 s before application DATA generation begins."),
        ("Drain", "Post-cutoff time allowing in-flight ACKs, reports, and deliveries to resolve."),
        ("ProtocolChannelModel", "UnetStack channel model capturing range, propagation delay, interference, collision, and configured detection/decoding probability."),
        ("Detection probability", "Configured chance that a frame is detected; 0.96 in the moderate scenario."),
        ("Decoding probability", "Configured chance that a detected frame can be decoded; 0.94 in the moderate scenario."),
        ("Collision", "Overlapping receptions that prevent successful decoding under the channel/model rules."),
        ("Half duplex", "A node cannot transmit and receive at the same time."),
        ("Propagation delay", "Travel time of the acoustic signal; sound speed is configured as 1500 m/s."),
        ("Depth case", "Node C is placed at 15 m or 1000 m; depth changes geometry and timing, not the configured probabilities."),
    ]
    story.extend([
        heading("4. Technical terms you should learn"),
        p("The most important viva distinction is this: application sending interval, modem bit rate, throughput, and reliability are four different quantities."),
        make_table([["Term", "Clear meaning in this project"]] + [list(row) for row in glossary], [44 * mm, 120 * mm], bold_first=True),
        PageBreak(),
    ])

    story.extend([
        heading("5. Experimental design and fairness"),
        make_table([
            ["Item", "Value"],
            ["Simulator", "UnetStack 7.0.0 discrete-event simulation"],
            ["Channel", "ScenarioChannelModel based on ProtocolChannelModel; moderate pDetection=0.96, pDecoding=0.94"],
            ["Topology", "A=(0 km,0,-15 m), B=(1 km,0,-15 m), C=(2 km,0,-depth)"],
            ["Depth cases", "C at 15 m and 1000 m"],
            ["Modem configuration", "2400 bit/s; 256-byte frame length; 64-byte DATA payload"],
            ["Warm-up / measurement", "60 s / 180 s, followed by a bounded drain"],
            ["Fixed mode", "3000 ms, ACK every original, no application retry"],
            ["Proposed", "Frozen candidate w2-e4-c3"],
            ["Screening", "Seeds 181-185; 280 units"],
            ["Calibration", "Seeds 201-210; 112 units"],
            ["Held-out evaluation", "Seeds 211-230; 80 units"],
        ], [48 * mm, 116 * mm], bold_first=True),
        heading("Fair-comparison rule", 2),
        p("For each paired seed, fixed and proposed use the same topology, payload, moderate channel, warm-up, measurement duration, node destination pattern, and random seed. Only the application-layer control protocol changes."),
        heading("Metric equations", 2),
    ])
    story.extend(code_block(
        "PDR (%) = 100 x unique delivered / unique generated\n"
        "Useful throughput (bit/s) = unique delivered x 64 bytes x 8 / 180 seconds\n"
        "Confirmed loss (%) = 100 - PDR (%)\n"
        "Retry overhead (%) = 100 x retry DATA attempts / all DATA attempts"
    ))
    story.extend([
        Spacer(1, 3 * mm),
        heading("Success gate", 2),
        p("At both depths, the point estimate had to reach at least +5% useful throughput and +5 PDR percentage points versus fixed, and the paired 95% interval had to exclude zero. The final evaluation is not a single selected run: it uses 20 paired held-out seeds per depth."),
        PageBreak(),
    ])

    result_rows = [["Depth", "Mode", "Generated", "Attempts", "Retries", "Delivered", "PDR", "Throughput", "Retry OH"]]
    for label, row in [("15 m", fixed15), ("15 m", proposed15), ("1000 m", fixed1000), ("1000 m", proposed1000)]:
        result_rows.append([
            label, row["approach"].title(), fmt(row, "unique_messages_generated"),
            fmt(row, "transmission_attempts"), fmt(row, "retry_attempts"),
            fmt(row, "unique_messages_delivered"), f"{fmt(row, 'pdr_pct')}%",
            f"{fmt(row, 'throughput_bps')} bit/s", f"{fmt(row, 'retry_overhead_pct')}%",
        ])
    effect_rows = [
        ["Depth", "Throughput gain (95% CI)", "PDR gain (95% CI)", "Gate"],
        ["15 m", f"+{fmt(effect15, 'throughput_change_pct')}% (+{fmt(effect15, 'throughput_ci95_low')} to +{fmt(effect15, 'throughput_ci95_high')})", f"+{fmt(effect15, 'pdr_change_pp')} pp (+{fmt(effect15, 'pdr_ci95_low')} to +{fmt(effect15, 'pdr_ci95_high')})", "PASS"],
        ["1000 m", f"+{fmt(effect1000, 'throughput_change_pct')}% (+{fmt(effect1000, 'throughput_ci95_low')} to +{fmt(effect1000, 'throughput_ci95_high')})", f"+{fmt(effect1000, 'pdr_change_pp')} pp (+{fmt(effect1000, 'pdr_ci95_low')} to +{fmt(effect1000, 'pdr_ci95_high')})", "PASS"],
    ]
    story.extend([
        heading("6. Final held-out results"),
        p("All values below come from the validated held-out evaluation matrix, not from screening or calibration."),
        make_table(result_rows, [17 * mm, 20 * mm, 19 * mm, 18 * mm, 15 * mm, 18 * mm, 18 * mm, 29 * mm, 20 * mm]),
        Spacer(1, 5 * mm),
        make_table(effect_rows, [20 * mm, 57 * mm, 59 * mm, 25 * mm]),
        heading("Interpretation", 2),
        p("At 15 m, proposed v3 delivered an average of 46.85 unique messages instead of 36.05, raising useful throughput from 102.54 to 133.26 bit/s. At 1000 m, it delivered 46.45 instead of 37.45, raising throughput from 106.52 to 132.12 bit/s. Proposed mode used about 5.2-5.4% of its DATA attempts for bounded recovery."),
        p("The result is a protocol improvement, not a faster modem. Both modes retain the same 2400 bit/s modem setting. The improvement comes from how application traffic, acknowledgements, and selective recovery use the simulated network."),
        add_figure.__doc__ if False else Spacer(1, 1),
    ])
    add_figure(story, MATLAB_FIGURES / "matlab_final_dashboard.png", "Figure 1. MATLAB dashboard recreated from validated final CSV summaries. The blue and orange bars use both color and direct labels/position; n=20 paired seeds per depth.", 118)
    story.append(PageBreak())

    story.extend([
        heading("7. Result graphs and what each one means"),
        heading("7.1 Absolute useful throughput", 2),
    ])
    add_figure(story, MATLAB_FIGURES / "matlab_throughput.png", "Figure 2. Mean useful throughput. Proposed v3 is higher at both tested depths. Bars begin at zero.", 97)
    story.extend([
        heading("7.2 Paired throughput improvement", 2),
    ])
    add_figure(story, MATLAB_FIGURES / "matlab_throughput_gain.png", "Figure 3. Proposed-versus-fixed percentage effect with paired bootstrap 95% confidence intervals and the +5% project target.", 97)
    story.append(PageBreak())
    story.extend([
        heading("7.3 Packet-delivery ratio", 2),
    ])
    add_figure(story, MATLAB_FIGURES / "matlab_pdr.png", "Figure 4. PDR counts unique delivered messages over unique generated messages. Proposed v3 is more reliable at both depths.", 97)
    story.extend([
        heading("7.4 Paired reliability improvement", 2),
    ])
    add_figure(story, MATLAB_FIGURES / "matlab_pdr_gain.png", "Figure 5. PDR improvement in percentage points with paired bootstrap 95% confidence intervals and the +5-point target.", 97)
    story.append(PageBreak())
    story.extend([
        heading("7.5 Confirmed loss and retry overhead", 2),
    ])
    add_figure(story, MATLAB_FIGURES / "matlab_packet_loss.png", "Figure 6. Confirmed packet loss equals 100 - PDR. Lower is better.", 88)
    add_figure(story, MATLAB_FIGURES / "matlab_retry_overhead.png", "Figure 7. Proposed mode spends only about 5.2-5.4% of DATA attempts on bounded retry; fixed mode has no application retry.", 88)
    story.append(PageBreak())
    story.extend([
        heading("7.6 RTT and timeout diagnostics", 2),
        p("RTT and timeout ratios are diagnostic signals, but the ACK policy differs between modes: fixed requests every original ACK, while proposed samples original ACKs and always ACKs retries. Therefore, compare them with that protocol context rather than treating them as identical measurement populations."),
    ])
    add_figure(story, MATLAB_FIGURES / "matlab_average_rtt.png", "Figure 8. Mean RTT of matched ACK samples under each protocol's declared ACK policy.", 88)
    add_figure(story, MATLAB_FIGURES / "matlab_timeout_ratio.png", "Figure 9. ACK deadline-expiration ratio. A timeout is not automatically confirmed DATA loss.", 88)
    story.append(PageBreak())

    story.extend([
        heading("8. Depth question: does deeper always mean more throughput?"),
        p("No. Depth can change 3D distance, propagation delay, and collision alignment, but it does not universally increase throughput. In this experiment, A and B remain at 15 m and C moves from 15 m to 1000 m while staying 2 km away horizontally."),
        make_table([
            ["Mode", "1000 m - 15 m throughput", "95% CI", "Conclusion"],
            ["Fixed", f"{fmt(depth_fixed, 'throughput_change_bps', 2)} bit/s", f"{fmt(depth_fixed, 'throughput_ci95_low', 2)} to {fmt(depth_fixed, 'throughput_ci95_high', 2)}", "Positive in this fixed-mode experiment"],
            ["Proposed", f"{fmt(depth_proposed, 'throughput_change_bps', 2)} bit/s", f"{fmt(depth_proposed, 'throughput_ci95_low', 2)} to +{fmt(depth_proposed, 'throughput_ci95_high', 2)}", "Inconclusive because the interval crosses zero"],
        ], [27 * mm, 47 * mm, 43 * mm, 47 * mm]),
    ])
    add_figure(story, MATLAB_FIGURES / "matlab_depth_effect.png", "Figure 10. Paired depth effect. The proposed interval crosses zero, so the experiment does not support a universal depth increase.", 105)
    story.extend([
        p("Correct TA sentence: Changing receiver depth affected geometry and collision timing. Fixed throughput increased by 3.88% in this specific experiment, but proposed throughput showed no statistically supported depth increase. Therefore, deeper placement does not universally guarantee higher throughput.", "Calloutx"),
        p("The moderate channel model keeps detection probability at 0.96 and decoding probability at 0.94 for both depths. It does not automatically model thermoclines, salinity profiles, pressure effects, or depth-dependent sound-speed refraction.", "Warningx"),
        PageBreak(),
    ])

    story.extend([
        heading("9. Code architecture and how to implement it yourself"),
        make_table([
            ["File", "What you implement or inspect"],
            ["simulations/experiment.groovy", "Topology, channel/model selection, modem settings, finite duration, run manifest"],
            ["scripts/adaptive-setup-a.groovy", "Sender node stack and AdaptiveExperimentAgent"],
            ["scripts/adaptive-setup-b.groovy", "Receiver stack and AdaptiveExperimentAgent"],
            ["classes/ExperimentConfig.groovy", "Read/validate environment variables and freeze them in a manifest"],
            ["classes/ProtocolCodec.groovy", "Encode/decode DATA, ACK, report request, and receiver report"],
            ["classes/ExperimentState.groovy", "Track unique IDs separately from transmission attempts"],
            ["classes/ReceiverFeedbackState.groovy", "Store deliveries and produce immutable snapshots"],
            ["classes/RetryScheduler.groovy", "ACK policy, retry queue, cadence, cap, one-retry rule, interval latch"],
            ["classes/AdaptiveRateController.groovy", "Four penalties, frozen weights, thresholds, candidate interval"],
            ["classes/AdaptiveExperimentAgent.groovy", "Paced send loop, receive logic, timeouts, reports, logging"],
            ["classes/ScenarioChannelModel.groovy", "Good/moderate/poor/step detection and decoding probabilities"],
            ["analysis/run_experiments.py", "Construct paired run matrix and execute bin/unet.bat"],
            ["analysis/analyze_results.py", "Recalculate metrics, paired bootstrap effects, success gates, Python figures"],
            ["analysis/analyze_final_results.m", "Read validated summaries and generate MATLAB PNG/vector-PDF figures"],
        ], [52 * mm, 112 * mm], bold_first=True),
        heading("Implementation order", 2),
        bullet("Start with the fixed 3000 ms path and unique sequence logging."),
        bullet("Add protocol encoding and receiver unique-delivery state."),
        bullet("Add immutable window snapshots and distinguish timeout from confirmed loss."),
        bullet("Add sparse ACK selection and one paced scheduler shared by originals and retries."),
        bullet("Add retry cadence, cap, and per-ID attempt limit."),
        bullet("Add the weighted controller and latch interval for a full original window."),
        bullet("Run paired seeds and validate each run manifest before analysis."),
        heading("Core pseudocode", 2),
    ])
    story.extend(code_block(
        "repeat until measurement cutoff:\n"
        "    interval = latched interval for current original window\n"
        "    if proposed and retry queue eligible after 4 new originals:\n"
        "        send one queued ID as attempt 2 with ACK requested\n"
        "    else:\n"
        "        create one new stable sequence ID\n"
        "        request ACK if fixed or original position is 9/10 or 10/10\n"
        "        send attempt 1; update original-window state\n"
        "\n"
        "on receiver snapshot:\n"
        "    freeze first valid snapshot for receiver/window\n"
        "    missing = expected IDs - delivered IDs\n"
        "    enqueue sorted missing IDs subject to cap=3 and attempts<=2\n"
        "\n"
        "on resolved window:\n"
        "    score = 0.15*RTT + 0.55*confirmed_loss + 0.15*ACK_failure + 0.15*timeout\n"
        "    choose next allowed interval and latch it for the next original window"
    ))
    story.append(PageBreak())

    story.extend([
        heading("10. Exact UnetStack and analysis commands"),
        heading("10.1 Open the project root", 2),
    ])
    story.extend(code_block('Set-Location "C:\\Users\\nikhi\\OneDrive\\Documents\\Desktop\\LAMDI\\CN PROJECT\\unet-7.0.0"'))
    story.extend([
        heading("10.2 Verify the tools", 2),
    ])
    story.extend(code_block(
        "java -version\n"
        "python --version\n"
        ".\\bin\\unet.bat\n"
        "matlab -batch \"disp(version)\""
    ))
    story.extend([
        heading("10.3 Run one fixed demonstration (unused seed 231)", 2),
    ])
    story.extend(code_block(
        "$env:ADR_MODE = \"fixed\"\n"
        "$env:ADR_SCENARIO = \"moderate\"\n"
        "$env:ADR_DEPTH_CASE = \"depth15\"\n"
        "$env:ADR_SEED = \"231\"\n"
        "$env:ADR_MEASUREMENT_S = \"180\"\n"
        "$env:ADR_OUTPUT_DIR = \"results\\demo\\fixed-depth15-seed231\"\n"
        "& .\\bin\\unet.bat simulations\\experiment.groovy"
    ))
    story.extend([
        heading("10.4 Run the paired proposed demonstration", 2),
    ])
    story.extend(code_block(
        "$env:ADR_MODE = \"proposed\"\n"
        "$env:ADR_OUTPUT_DIR = \"results\\demo\\proposed-depth15-seed231\"\n"
        "$env:ADR_WEIGHTS = \"0.15,0.55,0.15,0.15\"\n"
        "$env:ADR_RETRY_EVERY_NEW = \"4\"\n"
        "$env:ADR_MAX_RETRIES_PER_WINDOW = \"3\"\n"
        "& .\\bin\\unet.bat simulations\\experiment.groovy"
    ))
    story.extend([
        p("Keep the same seed, depth, scenario, and duration for the paired demonstration. Seed 231 is outside the final held-out set and does not rewrite the reported evidence.", "Warningx"),
        heading("10.5 Run or validate the complete 80-unit final matrix", 2),
    ])
    story.extend(code_block(
        "python analysis/run_experiments.py evaluation `\n"
        "  --config results/v3/calibration/frozen-config.json `\n"
        "  --workers 8 `\n"
        "  --measurement 180"
    ))
    story.extend([
        heading("10.6 Recalculate summaries and Python figures", 2),
    ])
    story.extend(code_block(
        "python analysis/analyze_results.py `\n"
        "  --runs results/v3/runs/evaluation `\n"
        "  --output results/v3"
    ))
    story.extend([
        heading("10.7 Recreate final figures with MATLAB", 2),
    ])
    story.extend(code_block('matlab -batch "run(\'analysis/analyze_final_results.m\')"'))
    story.extend([
        p("Expected MATLAB completion marker: MATLAB_FINAL_ANALYSIS_COMPLETE followed by the results/v3/matlab_figures path."),
        PageBreak(),
    ])

    story.extend([
        heading("11. How UnetStack results become MATLAB graphs"),
        make_table([
            ["Stage", "Input", "Output"],
            ["UnetStack simulation", "Environment configuration and Groovy code", "Per-node event CSV plus manifest in an isolated run directory"],
            ["Python validation/analysis", "All evaluation run directories", "run_summary.csv, overall_comparison.csv, paired_effects.csv, depth_effects.csv, success.json"],
            ["MATLAB presentation", "Validated results/v3/summary CSV files", "Ten PNG figures and ten vector PDF figures in results/v3/matlab_figures"],
        ], [38 * mm, 61 * mm, 65 * mm]),
        heading("Important separation", 2),
        p("UnetStack creates network events. Python is the canonical statistical pipeline that validates run identity, computes unique-message metrics, performs paired bootstrap analysis, and writes machine-readable summary CSV files. MATLAB reads those validated CSV files and recreates the final presentation graphs. MATLAB does not invent or manually type the result values."),
        heading("MATLAB outputs", 2),
        make_table([
            ["Figure file", "Meaning"],
            ["matlab_final_dashboard", "Throughput, PDR, loss, and retry overhead overview"],
            ["matlab_throughput", "Absolute useful throughput"],
            ["matlab_throughput_gain", "Paired relative gain with 95% CI and +5% target"],
            ["matlab_pdr", "Absolute PDR"],
            ["matlab_pdr_gain", "Paired PDR-point gain with 95% CI and +5-point target"],
            ["matlab_packet_loss", "Confirmed loss"],
            ["matlab_retry_overhead", "Bounded retry attempt fraction"],
            ["matlab_average_rtt", "Average matched-ACK RTT"],
            ["matlab_timeout_ratio", "ACK deadline-expiration ratio"],
            ["matlab_depth_effect", "1000 m minus 15 m paired throughput effect"],
        ], [62 * mm, 102 * mm]),
        PageBreak(),
    ])

    story.extend([
        heading("12. What to show the TA in the lab"),
        make_table([
            ["Order", "Show", "Say"],
            ["1", "simulations/experiment.groovy", "This fixes topology, modem, duration, and manifest."],
            ["2", "classes/AdaptiveExperimentAgent.groovy", "This is the paced sender/receiver message logic."],
            ["3", "classes/RetryScheduler.groovy", "This enforces sparse ACKs, retry cadence, cap, one-retry rule, and interval latch."],
            ["4", "results/v3/calibration/frozen-config.json", "Parameters were frozen before held-out evaluation."],
            ["5", "results/v3/summary/overall_comparison.csv", "These are the exact final means."],
            ["6", "results/v3/summary/paired_effects.csv", "These are effect sizes and paired 95% intervals."],
            ["7", "results/v3/matlab_figures/matlab_final_dashboard.png", "MATLAB recreated these plots from validated CSV output."],
            ["8", "results/v3/matlab_figures/matlab_depth_effect.png", "Depth did not universally increase throughput."],
        ], [15 * mm, 67 * mm, 82 * mm]),
        heading("Two-minute viva explanation", 2),
        p("Our problem is that a fixed sending interval cannot react to long-delay, lossy underwater network conditions. The official baseline sends a 64-byte application message every 3000 ms, asks for an ACK for every original, and has no application retry. Our protocol keeps the same modem, MAC, topology, payload, and channel probabilities. It changes only application-layer traffic control."),
        p("Proposed v3 operates on ten-original windows. It requests two original ACKs per full window, freezes the receiver's first valid delivery snapshot, and retries only sequence IDs confirmed missing. One retry becomes eligible after four new originals, each source window permits at most three retries, and one sequence ID can be sent at most twice. We count unique IDs, so retries cannot artificially increase throughput or PDR."),
        p("We calibrated parameters on seeds 201-210, froze candidate w2-e4-c3, and evaluated untouched seeds 211-230 at 15 m and 1000 m. Proposed v3 improved useful throughput by 30.63% and 24.30%, and PDR by 22.48 and 19.26 percentage points. Every paired 95% bootstrap interval excluded zero. Retry overhead was about 5%. We do not claim that greater depth always improves throughput; that was positive only for fixed mode in this model and inconclusive for proposed mode."),
        heading("Likely questions and short answers", 2),
        make_table([
            ["Question", "Answer"],
            ["What is legacy?", "An older adaptive controller reacting to each ACK/timeout; it is not fixed and not the official final baseline."],
            ["What do the weights do?", "They set each normalized metric's influence on the controller score; confirmed loss gets 0.55 because receiver evidence is strongest."],
            ["Why not ACK every packet?", "ACK thinning reduces reverse-channel traffic and possible interference."],
            ["Can retries fake throughput?", "No. A retry keeps the same sequence ID, and useful metrics count each ID once."],
            ["Why use paired seeds?", "They hold stochastic conditions equal between modes, improving fairness and precision."],
            ["Does timeout equal loss?", "No. ACK may be lost/delayed while DATA arrived; the receiver snapshot confirms delivery."],
            ["Does deeper mean faster?", "Not universally. Depth changes geometry/timing; our proposed depth effect was inconclusive."],
            ["Where is MATLAB used?", "After UnetStack and Python validation, MATLAB reads final CSV summaries and exports the report graphs."],
        ], [51 * mm, 113 * mm]),
        PageBreak(),
    ])

    story.extend([
        heading("13. Limitations and future work"),
        heading("Limitations", 2),
        bullet("The evidence is simulation-specific and not a field-ocean measurement."),
        bullet("The protocol channel uses configured detection/decoding probabilities and does not model a measured depth-dependent sound-speed profile."),
        bullet("The final claim covers one topology, two depths, one payload size, one moderate scenario, and one measurement duration."),
        bullet("ACK-based RTT populations differ because fixed and proposed intentionally use different ACK policies."),
        bullet("The observed gains should not be generalized to every traffic load, modem, route length, or ocean environment without new controlled tests."),
        heading("Defensible future work", 2),
        bullet("Run a separate preregistered depth sensitivity study at multiple depths with unused seeds."),
        bullet("Use a measured or externally computed sound-speed/path-loss model while keeping the application protocol unchanged."),
        bullet("Evaluate more payload sizes, node counts, traffic loads, and mobility patterns."),
        bullet("Test energy per unique delivered bit, not only throughput and PDR."),
        bullet("Deploy the same Groovy protocol logic on compatible UnetStack modem hardware for field validation."),
        heading("Do not do this", 2),
        p("Do not change the validated channel or held-out data just to force a preferred depth trend. A new physical-channel study must be a separate experiment with new seeds and a declared model.", "Warningx"),
        PageBreak(),
    ])

    story.extend([
        heading("14. Evidence files and references"),
        heading("Repository evidence", 2),
        make_table([
            ["Artifact", "Path"],
            ["Frozen configuration", "results/v3/calibration/frozen-config.json"],
            ["All held-out run metrics", "results/v3/summary/run_summary.csv"],
            ["Final means", "results/v3/summary/overall_comparison.csv"],
            ["Paired effects", "results/v3/summary/paired_effects.csv"],
            ["Depth effects", "results/v3/summary/depth_effects.csv"],
            ["Success gates", "results/v3/summary/success.json"],
            ["Python figures", "results/v3/figures/"],
            ["MATLAB figures", "results/v3/matlab_figures/"],
            ["Verification record", "results/v3/verification/FINAL_VERIFICATION.md"],
            ["Demo commands", "docs/DEMO_RUNBOOK.md"],
        ], [50 * mm, 114 * mm]),
        heading("Background and tooling references", 2),
        bullet("M. Chitre, R. Bhatnagar, and W.-S. Soh, 'UnetStack: an Agent-based Software Stack and Simulator for Underwater Networks,' OCEANS 2014 MTS/IEEE. https://arl.nus.edu.sg/wp-content/publications/Oceans14unetstack.pdf"),
        bullet("UnetStack Handbook, 'Simulating networks' and ProtocolChannelModel documentation. https://unetstack.net/handbook/402_sim.html"),
        bullet("P. Casari and M. Zorzi, 'Protocol design issues in underwater acoustic networks,' Computer Communications, vol. 34, no. 17, 2011, pp. 2013-2025. https://doi.org/10.1016/j.comcom.2011.06.008"),
        bullet("T. Kassis, V. Agarwal, Y. He, D. Patel, and A. M. Brueckner, 'Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents,' arXiv:2609.00065, 2026. https://doi.org/10.48550/arXiv.2609.00065"),
        heading("Final conclusion", 2),
        p("Protocol v3 met the declared +5% throughput and +5-point reliability targets at both tested depths. The evidence supports the application-layer combination of sparse ACK sampling, immutable receiver delivery evidence, bounded selective retransmission, and controlled pacing under the evaluated UnetStack configuration. It does not support a universal claim that throughput always rises with depth."),
        PageBreak(),
    ])

    matlab_source = (ROOT / "analysis" / "analyze_final_results.m").read_text(encoding="utf-8")
    story.extend([
        heading("Appendix A. Complete MATLAB graph-generation code"),
        p("This is the exact verified MATLAB source used to create the figures in results/v3/matlab_figures. Run it from the repository root."),
    ])
    story.extend(code_block(matlab_source))
    story.append(PageBreak())

    story.extend([
        heading("Appendix B. Additional validated diagnostic graphs"),
        p("The following figures are generated by the canonical Python analyzer from the same held-out run set. They are secondary diagnostics; the primary fixed-versus-proposed claim is based on the summary tables and paired effects above."),
    ])
    diagnostics = [
        ("throughput_vs_time.png", "Figure B1. Useful throughput over simulated time for the final run collection."),
        ("throughput_vs_rtt.png", "Figure B2. Throughput versus RTT diagnostic; correlation is not proof of causation."),
        ("interval_depth15.png", "Figure B3. Proposed interval observations at 15 m."),
        ("interval_depth1000.png", "Figure B4. Proposed interval observations at 1000 m."),
        ("weighted_score_depth15.png", "Figure B5. Available resolved-window weighted-score observations at 15 m."),
        ("weighted_score_depth1000.png", "Figure B6. Available resolved-window weighted-score observations at 1000 m."),
    ]
    for index, (filename, caption) in enumerate(diagnostics):
        if index in (2, 4):
            story.append(PageBreak())
            story.append(heading("Appendix B. Additional diagnostics - continued", 2))
        add_figure(story, PYTHON_FIGURES / filename, caption, 82)

    return story


def build() -> Path:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUTPUT), pagesize=A4,
        rightMargin=18 * mm, leftMargin=18 * mm,
        topMargin=23 * mm, bottomMargin=18 * mm,
        title="Complete Project and Lab Handbook - Protocol v3",
        author="CN Mini Project Team",
        subject="Adaptive Data Rate Control for Underwater Acoustic Networks",
    )
    doc.build(build_story(), onFirstPage=page_header_footer, onLaterPages=page_header_footer)
    reader = PdfReader(str(OUTPUT))
    if len(reader.pages) < 10:
        raise RuntimeError("Unexpectedly short PDF")
    if any(not (page.extract_text() or "").strip() for page in reader.pages):
        raise RuntimeError("A PDF page contains no extractable text")
    print(f"PDF_COMPLETE {OUTPUT} pages={len(reader.pages)}")
    return OUTPUT


if __name__ == "__main__":
    build()
