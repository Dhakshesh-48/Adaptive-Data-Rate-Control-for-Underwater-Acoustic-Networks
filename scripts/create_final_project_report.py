from __future__ import annotations

import csv
import html
from pathlib import Path

from PIL import Image as PILImage
from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Flowable,
    Image,
    LongTable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf" / "Final_Project_Report_Adaptive_Data_Rate_Control.pdf"
SUMMARY = ROOT / "results" / "v3" / "summary"
FIGURES = ROOT / "results" / "v3" / "matlab_figures"

NAVY = colors.HexColor("#12324A")
BLUE = colors.HexColor("#0072B2")
ORANGE = colors.HexColor("#D55E00")
GREEN = colors.HexColor("#007A5E")
INK = colors.HexColor("#17212B")
MUTED = colors.HexColor("#556270")
PALE_BLUE = colors.HexColor("#EAF3F8")
PALE_GREEN = colors.HexColor("#E8F5EF")
PALE_ORANGE = colors.HexColor("#FCEFE7")
LINE = colors.HexColor("#AAB7C4")


def read_csv(name: str) -> list[dict[str, str]]:
    with (SUMMARY / name).open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def select(rows: list[dict[str, str]], **match: str) -> dict[str, str]:
    found = [row for row in rows if all(row[key] == value for key, value in match.items())]
    if len(found) != 1:
        raise ValueError(f"Expected one row for {match}, found {len(found)}")
    return found[0]


overall = read_csv("overall_comparison.csv")
paired = read_csv("paired_effects.csv")
depth_rows = read_csv("depth_effects.csv")
fixed15 = select(overall, depth_case="depth15", approach="fixed")
proposed15 = select(overall, depth_case="depth15", approach="proposed")
fixed1000 = select(overall, depth_case="depth1000", approach="fixed")
proposed1000 = select(overall, depth_case="depth1000", approach="proposed")
effect15 = select(paired, depth_case="depth15")
effect1000 = select(paired, depth_case="depth1000")
depth_fixed = select(depth_rows, mode="fixed")
depth_proposed = select(depth_rows, mode="proposed")


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
    fontSize=24, leading=30, textColor=NAVY, alignment=TA_CENTER, spaceAfter=9,
))
styles.add(ParagraphStyle(
    name="CoverSub", parent=styles["Normal"], fontName=BODY_FONT,
    fontSize=11.5, leading=16, textColor=MUTED, alignment=TA_CENTER, spaceAfter=12,
))
styles.add(ParagraphStyle(
    name="H1x", parent=styles["Heading1"], fontName=BOLD_FONT,
    fontSize=16.5, leading=20.5, textColor=NAVY, spaceBefore=4, spaceAfter=8,
))
styles.add(ParagraphStyle(
    name="H2x", parent=styles["Heading2"], fontName=BOLD_FONT,
    fontSize=12.2, leading=15.5, textColor=BLUE, spaceBefore=6, spaceAfter=5,
))
styles.add(ParagraphStyle(
    name="H3x", parent=styles["Heading3"], fontName=BOLD_FONT,
    fontSize=10.2, leading=13, textColor=GREEN, spaceBefore=5, spaceAfter=3,
))
styles.add(ParagraphStyle(
    name="Bodyx", parent=styles["BodyText"], fontName=BODY_FONT,
    fontSize=9.1, leading=13.1, textColor=INK, alignment=TA_JUSTIFY, spaceAfter=5,
))
styles.add(ParagraphStyle(
    name="Abstractx", parent=styles["BodyText"], fontName=BODY_FONT,
    fontSize=9.3, leading=13.7, textColor=INK, alignment=TA_JUSTIFY, leftIndent=8*mm,
    rightIndent=8*mm, spaceAfter=6,
))
styles.add(ParagraphStyle(
    name="Smallx", parent=styles["BodyText"], fontName=BODY_FONT,
    fontSize=7.5, leading=10.2, textColor=MUTED, spaceAfter=3,
))
styles.add(ParagraphStyle(
    name="Captionx", parent=styles["BodyText"], fontName=BODY_FONT,
    fontSize=7.5, leading=10.1, textColor=MUTED, spaceAfter=6,
))
styles.add(ParagraphStyle(
    name="Bulletx", parent=styles["BodyText"], fontName=BODY_FONT,
    fontSize=9, leading=12.6, leftIndent=12, firstLineIndent=-7,
    bulletIndent=3, textColor=INK, spaceAfter=3,
))
styles.add(ParagraphStyle(
    name="Calloutx", parent=styles["BodyText"], fontName=BOLD_FONT,
    fontSize=9.6, leading=14, textColor=colors.white, backColor=GREEN,
    borderPadding=8, spaceBefore=5, spaceAfter=7,
))
styles.add(ParagraphStyle(
    name="Notex", parent=styles["BodyText"], fontName=BODY_FONT,
    fontSize=8.6, leading=12.3, textColor=INK, backColor=PALE_ORANGE,
    borderColor=ORANGE, borderWidth=0.7, borderPadding=7, spaceBefore=4, spaceAfter=7,
))
styles.add(ParagraphStyle(
    name="Codex", parent=styles["Code"], fontName="Courier",
    fontSize=6.9, leading=8.5, leftIndent=5, textColor=colors.HexColor("#082F49"),
    spaceAfter=0.5,
))
styles.add(ParagraphStyle(
    name="TableHead", parent=styles["Normal"], fontName=BOLD_FONT,
    fontSize=7.2, leading=9.2, textColor=colors.white,
))
styles.add(ParagraphStyle(
    name="TableCell", parent=styles["Normal"], fontName=BODY_FONT,
    fontSize=7.1, leading=9.3, textColor=INK,
))
styles.add(ParagraphStyle(
    name="TableCellBold", parent=styles["Normal"], fontName=BOLD_FONT,
    fontSize=7.1, leading=9.3, textColor=INK,
))


class HorizontalRule(Flowable):
    def __init__(self, width: float):
        super().__init__()
        self.width = width
        self.height = 4

    def draw(self):
        self.canv.setStrokeColor(LINE)
        self.canv.setLineWidth(0.7)
        self.canv.line(0, 2, self.width, 2)


def safe(value: object) -> str:
    return html.escape(str(value), quote=False)


def p(text: str, style: str = "Bodyx") -> Paragraph:
    return Paragraph(text, styles[style])


def heading(text: str, level: int = 1) -> Paragraph:
    return p(safe(text), {1: "H1x", 2: "H2x", 3: "H3x"}[level])


def bullet(text: str) -> Paragraph:
    return Paragraph(safe(text), styles["Bulletx"], bulletText="-")


def cell(value: object, header: bool = False, bold: bool = False) -> Paragraph:
    style = "TableHead" if header else ("TableCellBold" if bold else "TableCell")
    return Paragraph(safe(value), styles[style])


def table(rows: list[list[object]], widths: list[float], *, bold_first: bool = False) -> LongTable:
    converted = []
    for row_index, row in enumerate(rows):
        converted.append([
            cell(value, header=row_index == 0, bold=bold_first and column_index == 0)
            for column_index, value in enumerate(row)
        ])
    result = LongTable(converted, colWidths=widths, repeatRows=1, hAlign="LEFT")
    result.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.35, LINE),
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE_BLUE]),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return result


def code_block(code: str) -> list[Paragraph]:
    blocks = []
    for line in code.rstrip().splitlines():
        visible = safe(line).replace(" ", "&nbsp;") or "&nbsp;"
        blocks.append(Paragraph(visible, styles["Codex"]))
    return blocks


def add_figure(story: list, name: str, caption: str, max_height_mm: float = 102) -> None:
    path = FIGURES / name
    if not path.is_file():
        raise FileNotFoundError(path)
    with PILImage.open(path) as source:
        width_px, height_px = source.size
    max_width = 174 * mm
    max_height = max_height_mm * mm
    scale = min(max_width / width_px, max_height / height_px)
    story.append(Image(str(path), width=width_px * scale, height=height_px * scale, hAlign="CENTER"))
    story.append(p(safe(caption), "Captionx"))


def fmt(row: dict[str, str], key: str, digits: int = 2) -> str:
    return f"{float(row[key]):.{digits}f}"


def header_footer(canvas, doc):
    canvas.saveState()
    page = canvas.getPageNumber()
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.5)
    canvas.line(18 * mm, 284 * mm, 192 * mm, 284 * mm)
    canvas.setFont(BOLD_FONT, 7.1)
    canvas.setFillColor(NAVY)
    canvas.drawString(18 * mm, 287 * mm, "Adaptive data-rate control for underwater acoustic networks")
    canvas.line(18 * mm, 13 * mm, 192 * mm, 13 * mm)
    canvas.setFont(BODY_FONT, 7.1)
    canvas.setFillColor(MUTED)
    canvas.drawString(18 * mm, 8 * mm, "Final report | UnetStack 7.0.0 | Protocol v3")
    canvas.drawRightString(192 * mm, 8 * mm, f"Page {page}")
    canvas.restoreState()


def build_story() -> list:
    story: list = []

    story += [
        Spacer(1, 16 * mm),
        p("Adaptive data-rate control for<br/>underwater acoustic networks", "CoverTitle"),
        p("Final report", "CoverSub"),
        Spacer(1, 5 * mm),
        table([
            ["Roll number", "Team member"],
            ["241CS132", "M. Dhakshesh Naidu"],
            ["241CS142", "Pratham M. Attavar"],
            ["241CS158", "Srikara Nikhil"],
        ], [42 * mm, 105 * mm], bold_first=True),
        Spacer(1, 9 * mm),
        p("CS301 Mini Project 2026-27", "CoverSub"),
        p("November 2, 2026", "CoverSub"),
        Spacer(1, 8 * mm),
        p(
            "Verified result: Protocol v3 increased useful throughput by 30.63% at 15 m and "
            "24.30% at 1000 m. It increased packet-delivery ratio by 22.48 and 19.26 percentage "
            "points. The comparison used 20 paired held-out seeds at each depth.",
            "Calloutx",
        ),
        p(
            "Language note. This report uses ASD-STE100-style controlled English. It uses short "
            "sentences, active voice, stable technical terms, and American spelling. The report "
            "does not claim certified compliance with ASD-STE100 Issue 9.",
            "Notex",
        ),
        PageBreak(),
    ]

    story += [
        heading("Abstract"),
        p(
            "Underwater acoustic networks have long propagation delays, low bandwidth, and packet "
            "loss. A fixed application sending interval cannot use network feedback. If the interval "
            "is too short, data and acknowledgment traffic can interfere. If the interval is too long, "
            "the network does not use available transmission opportunities. This project implements "
            "an application-layer adaptive data-rate protocol in UnetStack 7.0.0. The fixed baseline "
            "sends at a 3000 ms interval, requests an acknowledgment for each original message, and "
            "does not retry at the application layer. Protocol v3 uses ten-message feedback windows. "
            "It requests two original acknowledgments per window. A receiver snapshot identifies "
            "missing sequence identifiers. The sender can retry a confirmed missing message one time. "
            "The controller gives the largest weight to confirmed loss and uses smaller weights for "
            "round-trip time, acknowledgment failure, and timeout events. We tested the fixed and "
            "proposed modes with the same topology, channel, duration, payload, and random seeds. "
            "The held-out evaluation contains 80 runs. At 15 m, useful throughput increased from "
            f"{fmt(fixed15, 'throughput_bps')} to {fmt(proposed15, 'throughput_bps')} bit/s, and packet-delivery ratio increased from "
            f"{fmt(fixed15, 'pdr_pct')}% to {fmt(proposed15, 'pdr_pct')}%. At 1000 m, useful throughput increased from "
            f"{fmt(fixed1000, 'throughput_bps')} to {fmt(proposed1000, 'throughput_bps')} bit/s, and packet-delivery ratio increased from "
            f"{fmt(fixed1000, 'pdr_pct')}% to {fmt(proposed1000, 'pdr_pct')}%. All four paired 95% bootstrap intervals exclude zero. "
            "The result shows an improvement for the declared simulation. It does not prove that "
            "throughput always increases with water depth.",
            "Abstractx",
        ),
        heading("Report organization", 2),
        table([
            ["Section", "Content"],
            ["1", "Background, challenges, problem statement, and objectives"],
            ["2", "Literature review and research gap"],
            ["3", "Proposed protocol and design reasons"],
            ["4", "UnetStack implementation and pseudocode"],
            ["5", "Experiment, metrics, results, graphs, and limitations"],
            ["6", "Conclusion and future work"],
            ["Appendices", "Reproduction commands and controlled terminology"],
        ], [25 * mm, 135 * mm], bold_first=True),
        PageBreak(),
    ]

    story += [
        heading("1 Introduction"),
        heading("1.1 Background", 2),
        p(
            "Underwater nodes use acoustic communication because radio signals do not support long "
            "underwater links. Sound moves through water at approximately 1500 m/s. The low sound "
            "speed produces long propagation delays. Acoustic links also have limited bandwidth and "
            "variable loss [1, 4]. These properties make the timing of application traffic important."
        ),
        p(
            "A sender selects an application sending interval. This interval is the time between DATA "
            "opportunities. It is not the modem bit rate. A short interval can increase channel use, but "
            "it can also increase overlap between DATA frames, acknowledgments, and receiver reports. "
            "A long interval reduces overlap, but it can reduce useful throughput."
        ),
        p(
            "A fixed-rate sender does not change the interval. It is simple and repeatable. It cannot "
            "use round-trip time, delivery evidence, or timeout history. An adaptive sender uses this "
            "feedback to select the next interval. The feedback must be reliable. A missing "
            "acknowledgment does not prove that the DATA frame was lost. The acknowledgment itself can "
            "be delayed or lost."
        ),
        heading("1.2 Challenges and issues", 2),
        bullet("Long propagation delay makes feedback old when it arrives."),
        bullet("Limited bandwidth makes an acknowledgment for every DATA frame expensive."),
        bullet("A timeout can mean DATA loss, acknowledgment loss, or late feedback."),
        bullet("A retry can recover a message, but too many retries can increase congestion."),
        bullet("The controller must not count duplicate deliveries as new useful data."),
        bullet("A fair experiment must keep all non-controller conditions equal."),
        p(
            "The controller must balance speed and reliability. It must also keep its own feedback and "
            "recovery overhead small. These requirements are connected. A controller can show high raw "
            "transmission activity and still deliver little new information. For this reason, this "
            "project measures unique delivered payload bits."
        ),
        PageBreak(),
        heading("1.3 Existing approaches and their issues", 2),
        p(
            "Fixed-rate transmission uses one interval for the complete run. It gives a stable baseline, "
            "but it does not react to a changed network condition. Automatic Repeat reQuest uses "
            "acknowledgments and retransmissions. It can improve reliability, but long underwater "
            "round-trip times and reverse-channel traffic can increase its cost [2]."
        ),
        p(
            "Guo, Liu, and Feng proposed an adaptive transmission control method for a tree network. "
            "Their method uses topology and bit-error-rate feedback to schedule node transmission times "
            "[3]. It targets collision and energy reduction. It does not use the receiver-validated "
            "window protocol that this project uses. Casari and Zorzi show that underwater protocols "
            "must account for long delay, limited bandwidth, and the interaction between protocol layers "
            "[4]. UnetStack supplies an agent-based network stack and simulator for this work [5, 6]."
        ),
        heading("1.4 Problem statement", 2),
        p(
            "Design and evaluate an application-layer protocol that improves useful throughput and "
            "packet-delivery ratio over a fixed 3000 ms sender. Use receiver-validated feedback, sparse "
            "acknowledgments, and bounded selective retry. Keep the topology, channel, duration, payload, "
            "and random seed equal for each fixed-and-proposed pair."
        ),
        heading("1.5 Objectives", 2),
        bullet("Implement the fixed baseline and Protocol v3 in UnetStack 7.0.0."),
        bullet("Use receiver evidence to separate confirmed missing DATA from missing acknowledgment feedback."),
        bullet("Measure useful throughput, packet-delivery ratio, loss, retries, round-trip time, and timeouts."),
        bullet("Compare the protocols with paired held-out seeds at 15 m and 1000 m."),
        bullet("Recreate the final graphs in MATLAB from validated CSV files."),
        heading("1.6 Scope", 2),
        p(
            "The contribution is in the application layer. The project does not change modulation, "
            "coding, modem transmit power, the physical data rate, or CSMA. The final claim applies to "
            "the declared UnetStack simulation. It is not a field-trial claim."
        ),
        PageBreak(),
    ]

    story += [
        heading("2 Literature review"),
        heading("2.1 Fixed-rate transmission", 2),
        p(
            "A fixed-rate sender transmits at a constant application interval. It has low controller "
            "complexity. It also gives a repeatable reference. The main limit is direct. The sender does "
            "not change its behavior when delay or loss changes."
        ),
        table([
            ["Advantages", "Limitations"],
            ["Simple implementation", "No response to measured network conditions"],
            ["Predictable schedule", "A short interval can add traffic during a poor condition"],
            ["Clear baseline", "A long interval can leave transmission opportunities unused"],
        ], [80 * mm, 80 * mm]),
        heading("2.2 Multi-hop ARQ for underwater networks", 2),
        p(
            "Tan, Seah, and Doyle studied multi-hop ARQ for underwater acoustic networks [2]. ARQ "
            "uses acknowledgments to detect missing delivery and retransmits data. This mechanism can "
            "recover packets. The underwater propagation delay makes each feedback cycle long. A design "
            "that requests too many acknowledgments can use channel time that DATA frames need."
        ),
        table([
            ["Advantages", "Limitations"],
            ["Direct delivery feedback", "Acknowledgment traffic uses channel capacity"],
            ["Packet recovery", "Long feedback delay can slow a decision"],
            ["Known reliability method", "A missing acknowledgment does not always mean DATA loss"],
        ], [80 * mm, 80 * mm]),
        heading("2.3 Adaptive transmission control", 2),
        p(
            "Guo, Liu, and Feng proposed adaptive transmission control for an underwater acoustic sensor "
            "network [3]. Their mechanism receives bit-error-rate and topology information. It assigns "
            "transmission times to nodes in a tree. The goal is to reduce collisions, retransmissions, "
            "and energy use. The method shows that feedback can control underwater traffic timing."
        ),
        p(
            "The method needs topology and link-quality information for its schedule. It is not a direct "
            "replacement for an application protocol that runs with sequence identifiers, sparse "
            "acknowledgments, and receiver snapshots. Its evaluation also has a different objective. It "
            "measures energy reduction, while this project measures unique payload delivery."
        ),
        PageBreak(),
        heading("2.4 Protocol design for underwater networks", 2),
        p(
            "Akyildiz, Pompili, and Melodia describe the main underwater sensor-network challenges [1]. "
            "Casari and Zorzi analyze protocol design issues for underwater acoustic networks [4]. Both "
            "works explain why a terrestrial timing rule cannot be used without a check. Propagation "
            "delay, bandwidth, channel variability, and energy cost affect protocol behavior."
        ),
        p(
            "These works do not define the exact controller in this project. They define the network "
            "conditions that the controller must respect. The design must use bounded feedback. It must "
            "also measure useful delivery and not only transmission activity."
        ),
        heading("2.5 UnetStack", 2),
        p(
            "Chitre, Bhatnagar, and Soh describe UnetStack as an agent-based software stack and simulator "
            "for underwater networks [5]. The simulator supports protocol development with the same agent "
            "model that compatible modem systems can use. The UnetStack handbook defines the simulation "
            "and channel-model interfaces [6]. This project uses UnetStack 7.0.0 as the central tool."
        ),
        heading("2.6 Comparison and research gap", 2),
        table([
            ["Approach", "Feedback", "Recovery", "Main limit for this project"],
            ["Fixed rate", "None for rate selection", "None", "Cannot adapt"],
            ["Multi-hop ARQ [2]", "Acknowledgments", "Retransmission", "Feedback and retry cost"],
            ["ATC [3]", "BER and topology", "Schedule control", "Different state and objective"],
            ["Protocol guidance [1, 4]", "Design principles", "Not an algorithm", "No project-specific controller"],
            ["Protocol v3", "Sparse ACK plus receiver snapshot", "Bounded selective retry", "Requires receiver report state"],
        ], [31 * mm, 43 * mm, 39 * mm, 50 * mm], bold_first=True),
        p(
            "The gap is a simple application-layer protocol that uses receiver-validated delivery state "
            "and limits its own feedback and retry traffic. Protocol v3 addresses this gap. It keeps "
            "one paced DATA opportunity stream. It uses stable sequence identifiers. It gives each "
            "identifier a maximum of two attempts."
        ),
        PageBreak(),
    ]

    story += [
        heading("3 Proposed approach"),
        heading("3.1 System model", 2),
        p(
            "The simulation has three nodes. Node A sends 64-byte application messages. Node B is at a "
            "horizontal distance of 1 km. Node C is at a horizontal distance of 2 km. Nodes A and B are "
            "at 15 m depth. Node C is at 15 m or 1000 m depth. The sender alternates destinations."
        ),
        p(
            "The modem data rate is 2400 bit/s. The channel uses the moderate scenario. The detection "
            "probability is 0.96. The decoding probability is 0.94. Each run has a 60 s warm-up, a "
            "180 s measurement period, and a bounded drain period."
        ),
        heading("3.2 Fixed baseline", 2),
        p(
            "The fixed baseline uses a 3000 ms interval. It requests one acknowledgment for each original "
            "message. It does not do an application-layer retry. The fixed interval does not use RTT, "
            "loss, acknowledgment failure, or timeout measurements."
        ),
        heading("3.3 Protocol v3", 2),
        table([
            ["Function", "Protocol v3 rule", "Reason"],
            ["Feedback window", "10 original messages", "Use a stable observation unit"],
            ["Original ACK policy", "Request ACK for the last 2 originals", "Reduce reverse traffic"],
            ["Delivery evidence", "Freeze the first valid receiver snapshot", "Keep historical evidence stable"],
            ["Retry selection", "Retry only confirmed missing identifiers", "Do not retry delivered data"],
            ["Retry cadence", "One retry opportunity after 4 new originals", "Prevent a retry burst"],
            ["Retry cap", "Maximum 3 retries per source window", "Bound recovery overhead"],
            ["Per-ID cap", "Maximum 2 attempts", "Prevent repeated retransmission"],
            ["Interval update", "Select one frozen candidate for a full window", "Prevent mid-window change"],
        ], [36 * mm, 61 * mm, 66 * mm], bold_first=True),
        heading("3.4 Controller score", 2),
        p(
            "The controller converts four observations to penalties between 0 and 1. It calculates a "
            "weighted score. The frozen weights are 0.15 for RTT, 0.55 for confirmed loss, 0.15 for "
            "acknowledgment failure, and 0.15 for timeout. The weights sum to 1."
        ),
        p(
            "Score = 0.15 x RTT penalty + 0.55 x confirmed-loss penalty + 0.15 x ACK-failure "
            "penalty + 0.15 x timeout penalty."
        ),
        p(
            "Confirmed loss gets the largest weight because the receiver snapshot gives direct evidence "
            "about missing unique identifiers. A timeout is only a warning. It does not prove DATA loss."
        ),
        PageBreak(),
        heading("3.5 Candidate interval selection", 2),
        p(
            "The controller selects an interval from this frozen list: 2000, 2250, 2500, 2700, 3000, "
            "3375, 3750, 4500, or 6000 ms. A healthy score permits a shorter interval. A poor score "
            "selects a longer interval. The controller latches the selected interval for the next full "
            "window. The latch prevents one late event from changing the interval in the middle of a "
            "window."
        ),
        heading("3.6 Protocol algorithm", 2),
    ]
    story += code_block("""Algorithm 1: Protocol v3 at the sender
1. Set the current interval to 3000 ms.
2. Create the next unique sequence identifier.
3. Select B or C with the alternating destination rule.
4. If the message is in one of the last two positions of the window, request an ACK.
5. Send the original message in the shared paced opportunity stream.
6. Record ACK, RTT, timeout, and receiver-report events.
7. Freeze the first valid receiver snapshot for the completed receiver window.
8. Add each confirmed missing identifier to the deterministic retry queue.
9. After four new originals, permit one queued retry opportunity.
10. Do not send more than three retries for the source window.
11. Do not send more than two attempts for one identifier.
12. Calculate the weighted score when the window resolves.
13. Select and latch the next candidate interval.
14. Repeat until the measurement cutoff.""")
    story += [
        heading("3.7 Design justification", 2),
        bullet("Sparse acknowledgments reduce reverse-channel traffic."),
        bullet("Receiver snapshots distinguish missing DATA from missing feedback."),
        bullet("Selective retry uses an opportunity only for a confirmed missing identifier."),
        bullet("A retry cadence mixes recovery with new traffic."),
        bullet("Hard retry limits prevent an uncontrolled retry loop."),
        bullet("Unique-message accounting prevents duplicate delivery from increasing the result."),
        p(
            "The proposed method is an improvement over the fixed baseline. It is also an improvement "
            "over the earlier legacy controller in this repository. The legacy controller reacts to "
            "individual ACK and timeout events. Protocol v3 uses complete windows and receiver-validated "
            "delivery evidence. The final held-out claim compares fixed mode with Protocol v3."
        ),
        PageBreak(),
    ]

    story += [
        heading("4 Implementation"),
        heading("4.1 Tools and environment", 2),
        table([
            ["Item", "Value"],
            ["Network simulator", "UnetStack 7.0.0 community distribution"],
            ["Protocol code", "Groovy agents and setup scripts"],
            ["Experiment control", "Python run matrix and manifest validation"],
            ["Statistical analysis", "Python paired bootstrap analysis"],
            ["Final graphs", "MATLAB R2026b script"],
            ["Host used for final check", "Windows with bin\\unet.bat"],
        ], [48 * mm, 112 * mm], bold_first=True),
        heading("4.2 Code architecture", 2),
        table([
            ["Component", "Responsibility"],
            ["simulations/experiment.groovy", "Configure channel, modem, topology, duration, and run manifest"],
            ["ExperimentConfig.groovy", "Read and validate experiment parameters"],
            ["ProtocolCodec.groovy", "Encode and decode DATA, ACK, report request, and receiver report"],
            ["ExperimentState.groovy", "Store unique identifiers and attempts"],
            ["ReceiverFeedbackState.groovy", "Store delivery state and create immutable snapshots"],
            ["RetryScheduler.groovy", "Apply ACK policy, retry cadence, caps, and interval latch"],
            ["AdaptiveRateController.groovy", "Calculate penalties, score, and candidate interval"],
            ["AdaptiveExperimentAgent.groovy", "Send, receive, time, report, and log protocol events"],
            ["ScenarioChannelModel.groovy", "Set detection and decoding probabilities"],
            ["analysis/run_experiments.py", "Create paired matrices and run UnetStack"],
            ["analysis/analyze_results.py", "Validate runs and calculate final metrics"],
            ["analysis/analyze_final_results.m", "Read summary CSV files and export final figures"],
        ], [55 * mm, 105 * mm], bold_first=True),
        PageBreak(),
        heading("4.3 Component flow", 2),
        table([
            ["Stage", "Input", "Output"],
            ["Experiment configuration", "Environment variables and frozen JSON", "Validated parameters"],
            ["UnetStack simulation", "Groovy code, seed, mode, and depth", "Three event CSV files and manifest"],
            ["Run validation", "Manifest and event files", "Accepted paired run set"],
            ["Python analysis", "All 80 held-out runs", "Summary CSV files and bootstrap intervals"],
            ["MATLAB analysis", "Validated summary CSV files", "PNG and vector PDF graphs"],
            ["Final report", "Verified tables and graphs", "Submission PDF"],
        ], [40 * mm, 55 * mm, 65 * mm], bold_first=True),
        heading("4.4 Message and state rules", 2),
        p(
            "Each DATA message has a stable sequence identifier and an attempt number. Attempt 1 is the "
            "original. Attempt 2 is the only permitted retry. The receiver stores the sequence identifier "
            "in a set. Thus, two delivered attempts still count as one unique message."
        ),
        p(
            "The receiver report contains delivery evidence for a completed window. The sender accepts "
            "the first valid snapshot and does not rewrite it. This rule keeps the control observation "
            "stable when late DATA or late feedback arrives."
        ),
        heading("4.5 Retry scheduler", 2),
    ]
    story += code_block("""Algorithm 2: Bounded retry scheduler
1. Read the frozen receiver snapshot.
2. Compare expected identifiers with delivered identifiers.
3. Put confirmed missing identifiers in a sorted queue.
4. Count new originals after the last retry opportunity.
5. If the count is less than 4, send the next original.
6. If the count is 4 and the queue is not empty, select one retry.
7. Reject a retry if the window already used 3 retries.
8. Reject a retry if the identifier already used attempt 2.
9. Send the selected DATA item through the same paced stream.""")
    story += [
        heading("4.6 Validation controls", 2),
        bullet("Each run has an isolated output directory."),
        bullet("The manifest records mode, depth, seed, duration, weights, and protocol version."),
        bullet("The runner rejects a missing manifest or a missing node event file."),
        bullet("Fixed and proposed runs use the same seed for each pair."),
        bullet("Screening and calibration seeds do not enter the held-out result."),
        bullet("Python tests check metrics, calibration, and run-matrix behavior."),
        bullet("Groovy tests check controller, protocol, scheduler, scenario, state, and agent behavior."),
        PageBreak(),
    ]

    story += [
        heading("5 Results and analysis"),
        heading("5.1 Simulation parameters", 2),
        table([
            ["Parameter", "Value"],
            ["Topology", "A = 0 km, B = 1 km, C = 2 km horizontally"],
            ["Depth", "A and B at 15 m; C at 15 m or 1000 m"],
            ["Channel", "Moderate ProtocolChannelModel scenario"],
            ["Detection and decoding", "0.96 and 0.94"],
            ["Sound speed", "1500 m/s"],
            ["Modem data rate", "2400 bit/s"],
            ["Frame and payload", "256-byte frame length; 64-byte application payload"],
            ["Timing", "60 s warm-up; 180 s measurement; bounded drain"],
            ["Fixed protocol", "3000 ms; ACK for each original; no application retry"],
            ["Proposed protocol", "w2-e4-c3; frozen weights 0.15, 0.55, 0.15, 0.15"],
            ["Held-out seeds", "211 to 230"],
            ["Evaluation units", "20 seeds x 2 depths x 2 modes = 80 runs"],
        ], [50 * mm, 110 * mm], bold_first=True),
        heading("5.2 Data partitions", 2),
        table([
            ["Partition", "Seeds", "Purpose", "Units"],
            ["Screening", "181-185", "Explore candidate configurations", "280"],
            ["Calibration", "201-210", "Select and freeze one candidate", "112"],
            ["Held-out evaluation", "211-230", "Calculate the final fixed-versus-proposed result", "80"],
        ], [38 * mm, 30 * mm, 72 * mm, 20 * mm], bold_first=True),
        heading("5.3 Performance metrics", 2),
        p("Packet-delivery ratio = 100 x unique delivered messages / unique generated messages."),
        p("Useful throughput = unique delivered messages x 64 bytes x 8 / 180 seconds."),
        p("Confirmed loss = 100 - packet-delivery ratio."),
        p("Retry overhead = 100 x retry DATA attempts / all DATA attempts."),
        p(
            "The independent unit is one complete seeded run. Individual packets in one run are not "
            "independent experiments. The analysis calculates paired differences by seed. It obtains "
            "95% intervals by bootstrap resampling of paired run effects."
        ),
        PageBreak(),
        heading("5.4 Final held-out results", 2),
        table([
            ["Depth", "Mode", "Generated", "Attempts", "Retries", "Delivered", "PDR", "Throughput", "Retry OH"],
            ["15 m", "Fixed", fmt(fixed15, "unique_messages_generated"), fmt(fixed15, "transmission_attempts"), fmt(fixed15, "retry_attempts"), fmt(fixed15, "unique_messages_delivered"), fmt(fixed15, "pdr_pct") + "%", fmt(fixed15, "throughput_bps") + " bit/s", fmt(fixed15, "retry_overhead_pct") + "%"],
            ["15 m", "Proposed", fmt(proposed15, "unique_messages_generated"), fmt(proposed15, "transmission_attempts"), fmt(proposed15, "retry_attempts"), fmt(proposed15, "unique_messages_delivered"), fmt(proposed15, "pdr_pct") + "%", fmt(proposed15, "throughput_bps") + " bit/s", fmt(proposed15, "retry_overhead_pct") + "%"],
            ["1000 m", "Fixed", fmt(fixed1000, "unique_messages_generated"), fmt(fixed1000, "transmission_attempts"), fmt(fixed1000, "retry_attempts"), fmt(fixed1000, "unique_messages_delivered"), fmt(fixed1000, "pdr_pct") + "%", fmt(fixed1000, "throughput_bps") + " bit/s", fmt(fixed1000, "retry_overhead_pct") + "%"],
            ["1000 m", "Proposed", fmt(proposed1000, "unique_messages_generated"), fmt(proposed1000, "transmission_attempts"), fmt(proposed1000, "retry_attempts"), fmt(proposed1000, "unique_messages_delivered"), fmt(proposed1000, "pdr_pct") + "%", fmt(proposed1000, "throughput_bps") + " bit/s", fmt(proposed1000, "retry_overhead_pct") + "%"],
        ], [16*mm, 20*mm, 18*mm, 18*mm, 15*mm, 18*mm, 16*mm, 28*mm, 20*mm]),
        Spacer(1, 3 * mm),
        table([
            ["Depth", "Throughput change", "95% interval", "PDR change", "95% interval", "Gate"],
            ["15 m", f"+{fmt(effect15, 'throughput_change_pct')}%", f"+{fmt(effect15, 'throughput_ci95_low')} to +{fmt(effect15, 'throughput_ci95_high')}%", f"+{fmt(effect15, 'pdr_change_pp')} points", f"+{fmt(effect15, 'pdr_ci95_low')} to +{fmt(effect15, 'pdr_ci95_high')}", "PASS"],
            ["1000 m", f"+{fmt(effect1000, 'throughput_change_pct')}%", f"+{fmt(effect1000, 'throughput_ci95_low')} to +{fmt(effect1000, 'throughput_ci95_high')}%", f"+{fmt(effect1000, 'pdr_change_pp')} points", f"+{fmt(effect1000, 'pdr_ci95_low')} to +{fmt(effect1000, 'pdr_ci95_high')}", "PASS"],
        ], [20*mm, 30*mm, 38*mm, 30*mm, 34*mm, 15*mm], bold_first=True),
        p(
            "The success target was at least 5% more useful throughput and 5 percentage points more "
            "packet-delivery ratio at both depths. Each point estimate passed. Each paired interval "
            "excludes zero."
        ),
        Spacer(1, 1),
    ]
    add_figure(story, "matlab_final_dashboard.png", "Figure 1. Final MATLAB dashboard. Each value comes from the validated held-out summary files.", 96)
    story.append(PageBreak())

    story += [
        heading("5.5 Useful throughput", 2),
        p(
            f"At 15 m, Protocol v3 delivered {fmt(proposed15, 'unique_messages_delivered')} unique messages per run. The fixed mode delivered "
            f"{fmt(fixed15, 'unique_messages_delivered')}. Useful throughput increased from {fmt(fixed15, 'throughput_bps')} to "
            f"{fmt(proposed15, 'throughput_bps')} bit/s. The paired increase was {fmt(effect15, 'throughput_change_pct')}%."
        ),
        p(
            f"At 1000 m, Protocol v3 delivered {fmt(proposed1000, 'unique_messages_delivered')} unique messages per run. The fixed mode delivered "
            f"{fmt(fixed1000, 'unique_messages_delivered')}. Useful throughput increased from {fmt(fixed1000, 'throughput_bps')} to "
            f"{fmt(proposed1000, 'throughput_bps')} bit/s. The paired increase was {fmt(effect1000, 'throughput_change_pct')}%."
        ),
    ]
    add_figure(story, "matlab_throughput.png", "Figure 2. Mean useful throughput for fixed mode and Protocol v3.", 96)
    add_figure(story, "matlab_throughput_gain.png", "Figure 3. Paired useful-throughput change with 95% intervals and the 5% target.", 88)
    story.append(PageBreak())

    story += [
        heading("5.6 Packet delivery and confirmed loss", 2),
        p(
            f"At 15 m, packet-delivery ratio increased from {fmt(fixed15, 'pdr_pct')}% to {fmt(proposed15, 'pdr_pct')}%. The paired "
            f"change was {fmt(effect15, 'pdr_change_pp')} percentage points. At 1000 m, packet-delivery ratio increased from "
            f"{fmt(fixed1000, 'pdr_pct')}% to {fmt(proposed1000, 'pdr_pct')}%. The paired change was "
            f"{fmt(effect1000, 'pdr_change_pp')} percentage points."
        ),
        p(
            "The metric counts unique sequence identifiers. If an original and its retry both arrive, "
            "the receiver counts one delivered message. The retry cannot create a second useful delivery."
        ),
    ]
    add_figure(story, "matlab_pdr.png", "Figure 4. Packet-delivery ratio for fixed mode and Protocol v3.", 91)
    add_figure(story, "matlab_pdr_gain.png", "Figure 5. Paired packet-delivery-ratio change with 95% intervals and the 5-point target.", 86)
    story.append(PageBreak())

    story += [
        heading("5.7 Retry, RTT, and timeout diagnostics", 2),
        p(
            f"Protocol v3 used {fmt(proposed15, 'retry_overhead_pct')}% retry overhead at 15 m and "
            f"{fmt(proposed1000, 'retry_overhead_pct')}% at 1000 m. The retry scheduler kept this "
            "overhead bounded. Fixed mode used no application-layer retry."
        ),
        p(
            "RTT and timeout values are diagnostic values. Fixed mode requests an acknowledgment for "
            "each original. Protocol v3 requests two original acknowledgments per full window and an "
            "acknowledgment for each retry. The two modes therefore do not sample the same ACK population. "
            "Do not use the RTT or timeout result alone as the main reliability claim."
        ),
    ]
    add_figure(story, "matlab_retry_overhead.png", "Figure 6. Retry DATA attempts as a percentage of all DATA attempts.", 80)
    add_figure(story, "matlab_average_rtt.png", "Figure 7. Mean RTT for the ACK samples that each protocol requests.", 80)
    story.append(PageBreak())

    story += [
        heading("5.8 Effect of depth", 2),
        p(
            "Depth does not have a general rule that makes throughput increase. A depth change can change "
            "3D distance, propagation delay, and the timing of collisions. It does not automatically "
            "improve channel quality. In this experiment, the moderate detection and decoding "
            "probabilities stay equal at both depths."
        ),
        table([
            ["Mode", "1000 m minus 15 m", "95% interval", "Result"],
            ["Fixed", f"{float(depth_fixed['throughput_change_bps']):+.2f} bit/s", f"{float(depth_fixed['throughput_ci95_low']):+.2f} to {float(depth_fixed['throughput_ci95_high']):+.2f}", "Positive in this fixed-mode experiment"],
            ["Proposed", f"{float(depth_proposed['throughput_change_bps']):+.2f} bit/s", f"{float(depth_proposed['throughput_ci95_low']):+.2f} to {float(depth_proposed['throughput_ci95_high']):+.2f}", "Inconclusive because the interval includes zero"],
        ], [30*mm, 38*mm, 43*mm, 52*mm], bold_first=True),
    ]
    add_figure(story, "matlab_depth_effect.png", "Figure 8. Paired effect of the depth change on useful throughput.", 92)
    story += [
        p(
            "Correct interpretation: fixed throughput increased in this specific simulation. Protocol v3 "
            "did not show a supported increase. The experiment does not support the statement that "
            "throughput always increases when depth increases.",
            "Calloutx",
        ),
        PageBreak(),
        heading("5.9 Comparison with the reviewed approaches", 2),
        table([
            ["Method", "Rate decision", "Feedback load", "Recovery", "Measured result"],
            ["Fixed baseline", "No rate change", "ACK for each original", "None", "60.08% and 62.42% PDR"],
            ["Multi-hop ARQ concept [2]", "Not the main function", "ACK based", "Retransmission", "Not reimplemented"],
            ["ATC [3]", "BER and topology schedule", "Periodic link feedback", "Collision reduction", "Not reimplemented"],
            ["Protocol v3", "Receiver-validated weighted score", "2 original ACKs per 10-message window", "Bounded selective retry", "82.57% and 81.68% PDR"],
        ], [29*mm, 40*mm, 40*mm, 30*mm, 28*mm], bold_first=True),
        p(
            "The numerical comparison is only between fixed mode and Protocol v3. The literature methods "
            "used different simulations and metrics. The table compares mechanisms. It does not claim a "
            "numerical win over a method that this project did not implement."
        ),
        heading("5.10 Limitations", 2),
        bullet("The experiment uses a three-node simulated topology."),
        bullet("The channel scenario uses fixed detection and decoding probabilities."),
        bullet("The experiment does not model a measured sound-speed profile, salinity profile, or thermocline."),
        bullet("The experiment uses two receiver depths and one horizontal geometry."),
        bullet("The final evidence is simulation evidence, not sea-trial evidence."),
        bullet("RTT and timeout samples differ because the ACK policies differ."),
        bullet("Protocol v3 needs receiver-report state and more application logic than fixed mode."),
        heading("5.11 Reproducibility", 2),
        p(
            "The repository contains the simulation scripts, controller code, tests, frozen configuration, "
            "all 80 held-out run directories, summary CSV files, and MATLAB graph script. The final "
            "verification passed seven Groovy tests and 23 Python tests. A fresh analysis produced the "
            "same summary tables as the submitted result set."
        ),
        PageBreak(),
    ]

    story += [
        heading("6 Conclusion and future work"),
        p(
            "This project studied application-layer data-rate control for underwater acoustic networks. "
            "The fixed baseline used a 3000 ms interval, one acknowledgment request for each original "
            "message, and no application-layer retry. Protocol v3 used sparse acknowledgments, immutable "
            "receiver snapshots, a weighted network-condition score, and bounded selective retry. The "
            "implementation used UnetStack 7.0.0. Python validated the runs and calculated paired effects. "
            "MATLAB recreated the final graphs from the validated CSV files."
        ),
        p(
            "The held-out evaluation used 20 paired seeds at each of two depths. Protocol v3 increased "
            "useful throughput by 30.63% at 15 m and 24.30% at 1000 m. It increased packet-delivery ratio "
            "by 22.48 and 19.26 percentage points. The paired 95% intervals excluded zero. Retry overhead "
            "was approximately 5.2% to 5.4%. The results meet the project target for the declared "
            "simulation. They do not show that depth always increases throughput."
        ),
        p(
            "Future work must test larger and mobile topologies. It must use measured channel traces and "
            "more channel states. A field test must run the same protocol on compatible UnetStack modem "
            "hardware. Future tests must also measure energy use and control-byte cost."
        ),
        heading("References"),
        p("[1] I. F. Akyildiz, D. Pompili, and T. Melodia, \"Underwater acoustic sensor networks: Research challenges,\" Ad Hoc Networks, vol. 3, no. 3, pp. 257-279, 2005. doi: 10.1016/j.adhoc.2005.01.004."),
        p("[2] H.-P. Tan, W. K. G. Seah, and L. Doyle, \"A Multi-hop ARQ Protocol for Underwater Acoustic Networks,\" OCEANS 2007. doi: 10.1109/OCEANSE.2007.4302195."),
        p("[3] Z.-W. Guo, X.-D. Liu, and Y. Feng, \"An Adaptive Transmission Control Mechanism for Underwater Acoustic Sensor Network,\" 2008 IFIP International Conference on Network and Parallel Computing. doi: 10.1109/NPC.2008.33."),
        p("[4] P. Casari and M. Zorzi, \"Protocol design issues in underwater acoustic networks,\" Computer Communications, vol. 34, no. 17, pp. 2013-2025, 2011. doi: 10.1016/j.comcom.2011.06.008."),
        p("[5] M. Chitre, R. Bhatnagar, and W.-S. Soh, \"UnetStack: An agent-based software stack and simulator for underwater networks,\" OCEANS 2014. doi: 10.1109/OCEANS.2014.7003044."),
        p("[6] UnetStack, \"Unet handbook: Simulating networks,\" https://unetstack.net/handbook/402_sim.html, accessed November 2, 2026."),
        p("[7] ASD Simplified Technical English Maintenance Group, \"ASD-STE100 Simplified Technical English, Issue 9,\" January 15, 2025, https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf."),
        PageBreak(),
    ]

    story += [
        heading("Appendix A. Reproduction commands"),
        heading("A.1 Open the project root", 2),
    ]
    story += code_block(r'''Set-Location "<repository-root>"''')
    story += [heading("A.2 Run all Groovy tests", 2)]
    story += code_block(r'''Get-ChildItem tests\*.groovy | Sort-Object Name | ForEach-Object {
  & .\bin\unet.bat $_.FullName
}''')
    story += [heading("A.3 Run all Python tests", 2)]
    story += code_block(r'''python -m unittest discover -s tests -p "test_*.py" -v''')
    story += [heading("A.4 Run or validate the frozen held-out matrix", 2)]
    story += code_block(r'''python analysis\run_experiments.py evaluation `
  --config results\v3\calibration\frozen-config.json `
  --workers 8 --measurement 180''')
    story += [heading("A.5 Recreate the summaries", 2)]
    story += code_block(r'''python analysis\analyze_results.py `
  --runs results\v3\runs\evaluation `
  --output results\v3''')
    story += [heading("A.6 Recreate the MATLAB graphs", 2)]
    story += code_block(r'''matlab -batch "run('analysis/analyze_final_results.m')"''')
    story += [
        p(
            "Install the required Python graph package before the Python test or analysis command. The "
            "current analysis imports matplotlib. Use the dependency instructions supplied with the "
            "submission package.",
            "Notex",
        ),
        heading("A.7 Manual fixed-mode demo", 2),
    ]
    story += code_block(r'''$env:ADR_MODE = "fixed"
$env:ADR_SCENARIO = "moderate"
$env:ADR_DEPTH_CASE = "depth15"
$env:ADR_SEED = "231"
$env:ADR_MEASUREMENT_S = "180"
$env:ADR_OUTPUT_DIR = "results\demo\fixed-depth15-seed231"
& .\bin\unet.bat simulations\experiment.groovy''')
    story += [PageBreak()]

    story += [
        heading("Appendix B. ASD-STE100-style terminology"),
        p(
            "Use one technical term for one item. Do not change terms only to make the text sound "
            "different. The terms in this table are the preferred terms for the report and the viva."
        ),
        table([
            ["Preferred term", "Meaning", "Do not use as an equal term"],
            ["application sending interval", "Time between paced DATA opportunities", "physical data rate"],
            ["physical data rate", "Bit rate of the modem model", "application sending interval"],
            ["useful throughput", "Unique delivered payload bits per second", "raw modem rate"],
            ["packet-delivery ratio", "Unique delivered divided by unique generated", "ACK ratio"],
            ["fixed baseline", "Non-adaptive 3000 ms protocol", "legacy adaptive"],
            ["legacy adaptive controller", "Older per-event adaptive code path", "fixed baseline"],
            ["Protocol v3", "Windowed receiver-validated proposed protocol", "legacy"],
            ["timeout", "ACK deadline expired", "confirmed DATA loss"],
            ["confirmed loss", "Generated ID absent from receiver delivery evidence", "timeout"],
            ["attempt", "One transmission of a sequence identifier", "unique message"],
            ["unique message", "One application item with one stable identifier", "attempt"],
            ["retry overhead", "Retry attempts divided by all DATA attempts", "control overhead"],
            ["receiver snapshot", "Frozen delivery evidence for a receiver window", "ACK list"],
        ], [43 * mm, 75 * mm, 47 * mm], bold_first=True),
        heading("B.1 Writing rules used in this report", 2),
        bullet("Use one term for one item."),
        bullet("Use the same term each time the item occurs."),
        bullet("Use active voice when the actor is known."),
        bullet("Write one main instruction or claim in one sentence."),
        bullet("Use short sentences and short paragraphs."),
        bullet("Use American English spelling."),
        bullet("Define a project-specific technical noun before frequent use."),
        bullet("Do not use a timeout as a synonym for confirmed loss."),
        bullet("Do not use depth as a synonym for channel quality."),
        bullet("Give a number and a unit when the evidence has them."),
        p(
            "ASD-STE100 is a controlled language standard for technical documentation [7]. This report "
            "uses its clarity principles. The project terms are technical nouns. A human reviewer must "
            "use the complete Issue 9 dictionary and rules before a claim of full compliance."
        ),
        PageBreak(),
        heading("Appendix C. Short viva answers"),
        table([
            ["Question", "Controlled answer"],
            ["What is the problem?", "A fixed sender cannot use measured delay or delivery state. It can send too fast or too slowly."],
            ["What is the baseline?", "The baseline is fixed mode. It uses a 3000 ms interval and no application retry."],
            ["What is legacy?", "Legacy is an older adaptive controller. It is not the fixed baseline."],
            ["What do the weights do?", "The weights set the influence of four normalized penalties. Confirmed loss has the largest influence."],
            ["Why is the loss weight 0.55?", "The receiver snapshot gives direct evidence of missing unique messages."],
            ["Why do you request fewer ACKs?", "Sparse ACK requests reduce reverse-channel traffic."],
            ["Why do you retry?", "A bounded retry can recover a receiver-confirmed missing message."],
            ["Can retry inflate throughput?", "No. The receiver counts a sequence identifier one time."],
            ["What improved?", "Useful throughput and packet-delivery ratio improved at both tested depths."],
            ["How much did throughput improve?", "It improved by 30.63% at 15 m and 24.30% at 1000 m."],
            ["How much did PDR improve?", "It improved by 22.48 and 19.26 percentage points."],
            ["Does more depth always increase throughput?", "No. The proposed depth effect was inconclusive in this experiment."],
            ["What is the main limitation?", "The evidence comes from a three-node controlled simulation, not a sea trial."],
            ["Why is this a CN project?", "The controller changes application traffic and feedback behavior. It does not change the physical modem."],
        ], [51 * mm, 112 * mm], bold_first=True),
        Spacer(1, 5 * mm),
        p(
            "Final evidence boundary: the numerical gains apply to the declared UnetStack topology, "
            "moderate channel, paired held-out seeds, and 180 s measurement period.",
            "Calloutx",
        ),
    ]

    return story


def build() -> Path:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(OUTPUT), pagesize=A4,
        rightMargin=18 * mm, leftMargin=18 * mm,
        topMargin=18 * mm, bottomMargin=18 * mm,
        title="Adaptive data-rate control for underwater acoustic networks",
        author="241CS132, 241CS142, 241CS158",
        subject="CS301 final report, Protocol v3",
    )
    document.build(build_story(), onFirstPage=header_footer, onLaterPages=header_footer)
    reader = PdfReader(str(OUTPUT))
    if len(reader.pages) < 18:
        raise RuntimeError(f"Final report is shorter than expected: {len(reader.pages)} pages")
    if OUTPUT.stat().st_size < 250_000:
        raise RuntimeError("Final report file is unexpectedly small")
    return OUTPUT


if __name__ == "__main__":
    result = build()
    print(f"FINAL_REPORT_CREATED {result}")
