from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import copy

doc = Document()

# ── Page margins ────────────────────────────────────────────
for section in doc.sections:
    section.top_margin    = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin   = Cm(3.0)
    section.right_margin  = Cm(2.5)

# ── Colour palette ──────────────────────────────────────────
DARK_NAVY   = RGBColor(0x0D, 0x1B, 0x2A)
ACCENT_BLUE = RGBColor(0x1B, 0x6C, 0xA8)
MID_GREY    = RGBColor(0x55, 0x65, 0x78)
LIGHT_GREY  = RGBColor(0xF2, 0xF4, 0xF7)
WHITE       = RGBColor(0xFF, 0xFF, 0xFF)
PLACEHOLDER = RGBColor(0xCC, 0xD6, 0xE0)

# ── Helpers ─────────────────────────────────────────────────
def set_run_font(run, name="Calibri", size=11, bold=False, italic=False, color=None):
    run.font.name     = name
    run.font.size     = Pt(size)
    run.font.bold     = bold
    run.font.italic   = italic
    if color:
        run.font.color.rgb = color

def para_space(para, before=0, after=0, line_rule=None, line_val=None):
    pf = para.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after  = Pt(after)
    if line_rule:
        pf.line_spacing_rule = line_rule
        pf.line_spacing      = line_val

def shade_cell(cell, fill_hex):
    tc   = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd  = OxmlElement('w:shd')
    shd.set(qn('w:val'),   'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'),  fill_hex)
    tcPr.append(shd)

def set_cell_border(cell, **borders):
    tc   = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    for edge, attrs in borders.items():
        tag = OxmlElement(f'w:{edge}')
        for k, v in attrs.items():
            tag.set(qn(f'w:{k}'), v)
        tcBorders.append(tag)
    tcPr.append(tcBorders)

def add_divider(doc, color_hex="1B6CA8", thickness="12"):
    p    = doc.add_paragraph()
    pPr  = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bot  = OxmlElement('w:bottom')
    bot.set(qn('w:val'),   'single')
    bot.set(qn('w:sz'),    thickness)
    bot.set(qn('w:space'), '1')
    bot.set(qn('w:color'), color_hex)
    pBdr.append(bot)
    pPr.append(pBdr)
    para_space(p, before=2, after=6)
    return p

def add_section_heading(doc, number, title):
    p  = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    para_space(p, before=18, after=4)
    r1 = p.add_run(f"{number}  ")
    set_run_font(r1, size=14, bold=True, color=ACCENT_BLUE)
    r2 = p.add_run(title.upper())
    set_run_font(r2, size=14, bold=True, color=DARK_NAVY)
    add_divider(doc, color_hex="1B6CA8", thickness="8")

def add_body(doc, text, space_before=4, space_after=6):
    p = doc.add_paragraph()
    para_space(p, before=space_before, after=space_after)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r = p.add_run(text)
    set_run_font(r, size=11, color=DARK_NAVY)
    return p

def add_placeholder(doc, label, caption):
    """Draws a shaded box with dashed border as an image placeholder."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.style     = 'Table Grid'
    cell = tbl.cell(0, 0)
    cell.width    = Inches(5.5)
    shade_cell(cell, "EBF3FA")
    set_cell_border(cell,
        top    = {"val": "dashed", "sz": "12", "color": "1B6CA8"},
        bottom = {"val": "dashed", "sz": "12", "color": "1B6CA8"},
        left   = {"val": "dashed", "sz": "12", "color": "1B6CA8"},
        right  = {"val": "dashed", "sz": "12", "color": "1B6CA8"},
    )
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

    # icon line
    icon_p = cell.paragraphs[0]
    icon_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para_space(icon_p, before=28, after=4)
    icon_r = icon_p.add_run("[ IMAGE ]")
    set_run_font(icon_r, size=24, bold=True, color=ACCENT_BLUE)

    # label
    lbl_p = cell.add_paragraph()
    lbl_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para_space(lbl_p, before=4, after=4)
    lbl_r = lbl_p.add_run(label)
    set_run_font(lbl_r, size=11, bold=True, color=DARK_NAVY)

    # instruction
    inst_p = cell.add_paragraph()
    inst_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para_space(inst_p, before=2, after=28)
    inst_r = inst_p.add_run("(replace this placeholder with your actual screenshot)")
    set_run_font(inst_r, size=9, italic=True, color=MID_GREY)

    # caption below the table
    cap_p = doc.add_paragraph()
    cap_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para_space(cap_p, before=4, after=14)
    cap_r = cap_p.add_run(caption)
    set_run_font(cap_r, size=9, italic=True, color=MID_GREY)


# ════════════════════════════════════════════════════════════
# COVER PAGE
# ════════════════════════════════════════════════════════════

# Top accent bar via a 1×1 table
bar = doc.add_table(rows=1, cols=1)
bar.alignment = WD_TABLE_ALIGNMENT.CENTER
bar_cell = bar.cell(0, 0)
shade_cell(bar_cell, "0D1B2A")
bar_p = bar_cell.paragraphs[0]
para_space(bar_p, before=2, after=2)

doc.add_paragraph()  # spacer

# Course tag
tag_p = doc.add_paragraph()
tag_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
para_space(tag_p, before=48, after=4)
tag_r = tag_p.add_run("SELECTED TOPICS IN COMPUTER SCIENCE — EMBEDDED SYSTEMS")
set_run_font(tag_r, size=9, bold=True, color=ACCENT_BLUE)

# Main title
title_p = doc.add_paragraph()
title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
para_space(title_p, before=8, after=0)
t1 = title_p.add_run("RadarBot")
set_run_font(t1, name="Calibri Light", size=48, bold=False, color=DARK_NAVY)

# Title underline accent
title_div = doc.add_paragraph()
title_div.alignment = WD_ALIGN_PARAGRAPH.CENTER
para_space(title_div, before=0, after=6)
td_r = title_div.add_run("─────────────────────────────────")
set_run_font(td_r, size=14, color=ACCENT_BLUE)

# Subtitle
sub_p = doc.add_paragraph()
sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
para_space(sub_p, before=4, after=40)
sub_r = sub_p.add_run("Ultrasonic Radar System  ·  Project Report")
set_run_font(sub_r, size=16, italic=True, color=MID_GREY)

# Team block via table
team_tbl = doc.add_table(rows=1, cols=1)
team_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
team_cell = team_tbl.cell(0, 0)
shade_cell(team_cell, "EBF3FA")
set_cell_border(team_cell,
    top    = {"val": "single", "sz": "18", "color": "1B6CA8"},
    bottom = {"val": "single", "sz": "18", "color": "1B6CA8"},
    left   = {"val": "single", "sz": "18", "color": "1B6CA8"},
    right  = {"val": "single", "sz": "18", "color": "1B6CA8"},
)

team_label = team_cell.paragraphs[0]
team_label.alignment = WD_ALIGN_PARAGRAPH.CENTER
para_space(team_label, before=14, after=6)
tl_r = team_label.add_run("PROJECT TEAM")
set_run_font(tl_r, size=9, bold=True, color=ACCENT_BLUE)

for name in ["Seif Mohamed Fouad Makled", "Antoni Ashraf Mikhael"]:
    np = team_cell.add_paragraph()
    np.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para_space(np, before=2, after=2)
    nr = np.add_run(name)
    set_run_font(nr, size=13, bold=True, color=DARK_NAVY)

details_p = team_cell.add_paragraph()
details_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
para_space(details_p, before=8, after=14)
dr = details_p.add_run("Third Year  ·  CS-AI Program  ·  May 2026")
set_run_font(dr, size=10, italic=True, color=MID_GREY)

doc.add_page_break()


# ════════════════════════════════════════════════════════════
# SECTION 1 — PROJECT OVERVIEW
# ════════════════════════════════════════════════════════════
add_section_heading(doc, "01", "Project Overview")

add_body(doc,
    "RadarBot is a real-time proximity sensing and visualization system built entirely "
    "on a single Arduino board. At its core, a micro servo motor sweeps an HC-SR04 "
    "ultrasonic sensor across a 150-degree arc, firing sound pulses and measuring "
    "how long each echo takes to return. That round-trip time translates directly "
    "into distance — updated every 30 milliseconds, at every degree of rotation."
)
add_body(doc,
    "When something enters the 30-centimeter danger zone, a passive buzzer fires a "
    "2 kHz alarm. Simultaneously, the Arduino streams angle and distance data over "
    "USB serial to two separate software layers running on a connected PC: a "
    "Processing sketch that renders a classic green radar display, and a Python "
    "script that logs every reading to a local SQLite database for later analysis."
)
add_body(doc,
    "A joystick module adds a layer of interactivity — one button press hands the "
    "operator direct control over the servo angle, and another press gives it back "
    "to the automatic sweep. The project brings together sensor interfacing, PWM "
    "motor control, real-time serial communication, and multi-layer software "
    "integration in a way that is both practically functional and visually compelling."
)


# ════════════════════════════════════════════════════════════
# SECTION 2 — HARDWARE COMPONENTS
# ════════════════════════════════════════════════════════════
add_section_heading(doc, "02", "Hardware Components")

add_body(doc,
    "The system runs on off-the-shelf components, all wired through a single breadboard "
    "that acts as the shared power and ground bus. The table below lists each component "
    "and its role in the system."
)

hw_data = [
    ("Component",           "Role"),
    ("Arduino (Uno / Mega)",      "Central microcontroller — runs all firmware"),
    ("HC-SR04 Ultrasonic Sensor", "Measures distance via sound echo timing (Trig: Pin 8, Echo: Pin 9)"),
    ("SG90 Micro Servo Motor",    "Rotates the sensor tower across the scanning arc (Signal: Pin 10)"),
    ("Passive Buzzer",            "Piezo alarm — 2 kHz tone when object < 30 cm (Pin 7)"),
    ("Joystick Module",           "X-axis controls angle in manual mode; button toggles mode (A0, Pin 4)"),
    ("Breadboard + Cables",       "Power rail distribution and component interconnection"),
]

hw_tbl = doc.add_table(rows=len(hw_data), cols=2)
hw_tbl.style = 'Table Grid'
hw_tbl.alignment = WD_TABLE_ALIGNMENT.LEFT

for i, (c1, c2) in enumerate(hw_data):
    row = hw_tbl.rows[i]
    row.cells[0].width = Inches(2.1)
    row.cells[1].width = Inches(4.0)

    if i == 0:
        shade_cell(row.cells[0], "0D1B2A")
        shade_cell(row.cells[1], "0D1B2A")
        for cell, txt in zip(row.cells, [c1, c2]):
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            para_space(p, before=4, after=4)
            r = p.add_run(txt)
            set_run_font(r, size=10, bold=True, color=WHITE)
    else:
        fill = "F2F4F7" if i % 2 == 0 else "FFFFFF"
        shade_cell(row.cells[0], fill)
        shade_cell(row.cells[1], fill)
        for j, (cell, txt) in enumerate(zip(row.cells, [c1, c2])):
            p = cell.paragraphs[0]
            para_space(p, before=3, after=3)
            r = p.add_run(txt)
            bold = (j == 0)
            set_run_font(r, size=10, bold=bold, color=DARK_NAVY)

doc.add_paragraph()


# ════════════════════════════════════════════════════════════
# SECTION 3 — SYSTEM ARCHITECTURE
# ════════════════════════════════════════════════════════════
add_section_heading(doc, "03", "System Architecture")

add_body(doc,
    "RadarBot is structured across three distinct software layers, each with a clear "
    "responsibility. The Arduino is the only layer that talks directly to hardware — "
    "everything above it communicates through the USB serial port."
)

layers = [
    ("Arduino Firmware",
     "The on-device layer. It reads the ultrasonic sensor, drives the servo via PWM, "
     "monitors the joystick button for mode changes, and activates the buzzer when "
     "the distance threshold is crossed. Every 30 ms, it serialises the current angle "
     "and distance and writes them to the USB serial port at 9600 baud."),
    ("Processing — Radar Display",
     "A desktop sketch that listens on the same serial port and renders a radar "
     "visualization in real time: a sweeping green line, concentric range rings at "
     "20 cm intervals out to 100 cm, and a red marker wherever an object is detected. "
     "Distance and angle are shown numerically at the bottom of the screen."),
    ("Python + SQLite — Data Logger",
     "A Python script that reads the serial stream, parses each packet, and inserts "
     "a timestamped record into a local SQLite database (radar_logs.db) once per "
     "second. The database schema captures angle, distance, operating mode, and buzzer "
     "state — queryable with the SQL scripts in the SQL Queries folder."),
]

for title, body in layers:
    lp = doc.add_paragraph()
    para_space(lp, before=8, after=2)
    lr = lp.add_run(f"  {title}")
    set_run_font(lr, size=11, bold=True, color=ACCENT_BLUE)
    add_body(doc, f"      {body}", space_before=0, space_after=6)

add_body(doc,
    "One important constraint: Processing and the Python logger both open the same "
    "serial port, so only one can run at a time. This is expected behaviour — the "
    "operator closes the visualization when they want to log data, and vice versa.",
    space_before=6, space_after=8
)


# ════════════════════════════════════════════════════════════
# SECTION 4 — CIRCUIT DIAGRAM
# ════════════════════════════════════════════════════════════
add_section_heading(doc, "04", "Circuit Diagram")

add_body(doc,
    "The figure below shows the complete wiring layout as simulated in Wokwi. "
    "All component power lines connect to the breadboard's shared 5V rail, which "
    "is fed from the Arduino's onboard 5V pin. Ground lines share the breadboard's "
    "GND rail, tied back to the Arduino GND. Signal wires run directly between each "
    "component and its designated Arduino pin."
)

add_placeholder(doc,
    "[ Insert Circuit Diagram / Wokwi Simulation Screenshot Here ]",
    "Figure 1: Wokwi Circuit Simulation — Full Wiring Layout"
)


# ════════════════════════════════════════════════════════════
# SECTION 5 — PROCESSING RADAR UI
# ════════════════════════════════════════════════════════════
add_section_heading(doc, "05", "Processing Radar UI")

add_body(doc,
    "The Processing sketch renders a full-screen radar display modelled on classic "
    "military-style PPI (Plan Position Indicator) scopes. A bright green sweep line "
    "rotates in sync with the physical servo. Five concentric arcs mark the 20, 40, "
    "60, 80, and 100 centimetre range rings. When the sensor detects an object within "
    "range, a red line segment appears at the measured distance and holds briefly as "
    "the sweep continues past — leaving a trace that fades naturally with each pass."
)
add_body(doc,
    "An out-of-range reading (no echo within 25 ms) renders as an orange marker at "
    "the edge of the display rather than leaving a false close-range detection. Angle "
    "and distance are printed numerically at the bottom of the screen alongside the "
    "team name."
)

add_placeholder(doc,
    "[ Insert Processing Radar UI Screenshot Here ]",
    "Figure 2: Real-Time Radar Visualization — Processing Sketch"
)


# ════════════════════════════════════════════════════════════
# SECTION 6 — DATABASE LOGGING
# ════════════════════════════════════════════════════════════
add_section_heading(doc, "06", "Database Logging")

add_body(doc,
    "The Python logger connects to the Arduino's serial port at 9600 baud and reads "
    "incoming packets continuously. To avoid flooding the database with redundant data, "
    "it applies a one-second rate limit — writing exactly one record per second regardless "
    "of how fast the Arduino is transmitting. Each record carries five fields:"
)

schema_data = [
    ("Field",          "Type",    "Description"),
    ("timestamp",      "TEXT",    "ISO 8601 timestamp (microsecond precision)"),
    ("angle",          "INTEGER", "Servo angle in degrees (15 – 165)"),
    ("distance",       "INTEGER", "Measured distance in cm  (−1 = no echo / out of range)"),
    ("mode",           "INTEGER", "0 = Automatic sweep  |  1 = Manual joystick control"),
    ("buzzer_active",  "INTEGER", "0 = Buzzer OFF  |  1 = Buzzer ON"),
]

sc_tbl = doc.add_table(rows=len(schema_data), cols=3)
sc_tbl.style = 'Table Grid'
sc_tbl.alignment = WD_TABLE_ALIGNMENT.LEFT
col_widths = [Inches(1.5), Inches(1.0), Inches(3.6)]

for i, row_data in enumerate(schema_data):
    row = sc_tbl.rows[i]
    for j, (cell, txt) in enumerate(zip(row.cells, row_data)):
        cell.width = col_widths[j]
        if i == 0:
            shade_cell(cell, "1B6CA8")
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            para_space(p, before=4, after=4)
            r = p.add_run(txt)
            set_run_font(r, size=10, bold=True, color=WHITE)
        else:
            fill = "F2F4F7" if i % 2 == 0 else "FFFFFF"
            shade_cell(cell, fill)
            p = cell.paragraphs[0]
            para_space(p, before=3, after=3)
            r = p.add_run(txt)
            set_run_font(r, size=10, bold=(j == 0), color=DARK_NAVY)

doc.add_paragraph()
add_body(doc,
    "The SQL Queries folder ships five ready-made queries covering the most common "
    "analysis tasks: filtering by angle range, distance threshold, operating mode, "
    "buzzer state, and time window. DB Browser for SQLite is the recommended tool "
    "for browsing the database visually."
)

add_placeholder(doc,
    "[ Insert DB Browser / Database Screenshot Here ]",
    "Figure 3: SQLite Database — radar_logs Table (DB Browser for SQLite)"
)


# ════════════════════════════════════════════════════════════
# SECTION 7 — OPERATION MODES
# ════════════════════════════════════════════════════════════
add_section_heading(doc, "07", "Operation Modes")

modes = [
    ("Automatic Mode",
     "Default on startup. The servo steps one degree every 30 ms, bouncing between "
     "15° and 165°. The sensor fires at each step and the result is immediately "
     "streamed out over serial. No user input required — the radar runs on its own "
     "until the joystick button is pressed."),
    ("Manual Mode",
     "Activated by pressing the joystick button (Pin 4). The sweep stops and the "
     "joystick's X-axis takes over, mapping the analog range (0 – 1023) directly "
     "to servo angle (15° – 165°). The sensor still fires continuously at whatever "
     "angle the joystick is pointing. Another press of the button returns to automatic."),
    ("Buzzer Alarm",
     "Active in both modes. Whenever the measured distance is between 1 and 29 cm, "
     "the Arduino calls tone(7, 2000) — a 2 kHz pulse on the buzzer pin. "
     "The moment the object moves away or disappears, noTone(7) cuts it off immediately. "
     "A distance of −1 (no echo detected) is treated as out-of-range and does not "
     "trigger the alarm."),
]

for title, body in modes:
    mp = doc.add_paragraph()
    para_space(mp, before=8, after=2)
    mr = mp.add_run(f"  {title}")
    set_run_font(mr, size=11, bold=True, color=ACCENT_BLUE)
    add_body(doc, f"      {body}", space_before=0, space_after=6)


# ════════════════════════════════════════════════════════════
# SECTION 8 — CONCLUSION
# ════════════════════════════════════════════════════════════
add_section_heading(doc, "08", "Conclusion")

add_body(doc,
    "RadarBot turned out to be more than the sum of its parts. What started as a "
    "handful of cheap sensors and a breadboard became a system that operates across "
    "three software layers simultaneously — each one dependent on the others getting "
    "their timing and formatting exactly right."
)
add_body(doc,
    "The most demanding part was not the hardware, but the serial protocol: getting "
    "the Arduino, Processing, and Python to agree on data format, baud rate, and "
    "port access without stepping on each other. That constraint — only one program "
    "can own the port at a time — forced a clean architectural decision early on and "
    "shaped the rest of the design."
)
add_body(doc,
    "The end result is a working proximity radar: it sweeps, it detects, it alarms, "
    "it visualizes, and it logs. Every piece of functionality was built incrementally "
    "and tested against real hardware. That is exactly the kind of iterative, "
    "constraint-driven engineering that embedded systems demand."
)

# Bottom accent bar
doc.add_paragraph()
end_bar = doc.add_table(rows=1, cols=1)
end_bar.alignment = WD_TABLE_ALIGNMENT.CENTER
end_cell = end_bar.cell(0, 0)
shade_cell(end_cell, "0D1B2A")
end_p = end_cell.paragraphs[0]
end_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
para_space(end_p, before=6, after=6)
end_r = end_p.add_run("RadarBot  ·  Third Year CS-AI  ·  Seif Makled & Antoni Mikhael  ·  May 2026")
set_run_font(end_r, size=9, color=WHITE)

# ── Save ────────────────────────────────────────────────────
out = r"c:\Users\SeifMaklad\OneDrive\Desktop\Ultrasonic-Radar-System\RadarBot Report.docx"
doc.save(out)
print(f"Saved: {out}")
