"""Build the methodology sample as editable PPTX, PDF, previews and speaker notes.

Uses the existing matplotlib/Pillow environment; does not alter submission code.
The PPTX is converted to native Keynote by convert_methodology_sample.applescript.
"""
from pathlib import Path
import csv
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
import textwrap
import zipfile
from xml.sax.saxutils import escape
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'presentation/methodology_sample'
OUT.mkdir(exist_ok=True)
W, H = 13.333333, 7.5
INK, BG, RED, TEAL, GRAY, LIGHT = '142D39', 'F7F5F0', 'CF4939', '147C70', '526671', 'E8ECE8'
FONT = 'Arial'
FONT_FILE = font_manager.findfont(font_manager.FontProperties(family=FONT))
BOLD_FILE = font_manager.findfont(font_manager.FontProperties(family=FONT, weight='bold'))
SLIDES = []


def slide(title, tag, timing, say, support, cue='', dark=False, appendix=False):
    s = dict(title=title, tag=tag, timing=timing, say=say, support=support,
             cue=cue, dark=dark, appendix=appendix, items=[])
    SLIDES.append(s)
    color = BG if dark else INK
    text(s, tag.upper(), .62, .42, 11.8, 12, TEAL if not dark else '8FD8C8', bold=True)
    if not dark:
        text(s, title, .62, 1.01, 12.05, 32, color, bold=True)
    rect(s, .62, 7.01, 12.08, .012, 'B8C3C3' if not dark else '46606A')
    text(s, 'NAMA  /  Methodology & generalization', .62, 7.14, 9.5, 10, GRAY if not dark else 'B4C6C8')
    text(s, f'{len(SLIDES):02d}  /  ' + ('SUPPORT' if appendix else timing), 10.4, 7.14, 2.3, 10,
         GRAY if not dark else 'B4C6C8', align='right')
    return s


def rect(s, x, y, w, h, fill, stroke=None):
    s['items'].append(dict(kind='rect', x=x, y=y, w=w, h=h, fill=fill, stroke=stroke))


def line(s, x1, y1, x2, y2, color=GRAY, width=1.2):
    s['items'].append(dict(kind='line', x=x1, y=y1, x2=x2, y2=y2, color=color, width=width))


def text(s, value, x, y, w, size=20, color=INK, bold=False, align='left', h=None):
    font = ImageFont.truetype(BOLD_FILE if bold else FONT_FILE, round(size * 2))
    max_px = w * 144
    lines = []
    for para in str(value).split('\n'):
        current = ''
        for word in para.split():
            trial = (current + ' ' + word).strip()
            if current and font.getlength(trial) > max_px:
                lines.append(current)
                current = word
            else:
                current = trial
        lines.append(current)
    height = h or max(.20, len(lines) * size / 72 * 1.18 + .05)
    assert len(lines) * size / 72 * 1.10 <= height + .01, (value, height)
    assert x + w <= W + .01 and y + height <= H + .01, (value, x, y, w, height)
    s['items'].append(dict(kind='text', text='\n'.join(lines), x=x, y=y, w=w, h=height,
                           size=size, color=color, bold=bold, align=align))


def card(s, x, y, w, h, label, body, accent=TEAL, size=20):
    rect(s, x, y, w, h, 'FFFFFF')
    rect(s, x, y, .045, h, accent)
    text(s, label, x+.20, y+.18, w-.40, 16, accent, bold=True)
    text(s, body, x+.20, y+.63, w-.40, size)


def build_content():
    s = slide('Recover rules. Build evidence. Reuse the method.', 'Our approach / Team NAMA', '0:00–0:15',
        'Our approach is a reusable discovery loop. We start with a readable rule, use the mismatches to guide experiments, and turn supported findings into deterministic Python. AI helps investigate; exact comparisons decide what we keep.',
        'Opening goes directly to our approach: assume the jury knows the challenge. Assistants used in development include Claude Code and Codex; the submitted calculations are deterministic. This is a human-guided toolkit, not autonomous recovery of arbitrary formulas.',
        'Face camera; then bring up the three-step stack.', dark=True)
    text(s, 'Recover rules.\nBuild evidence.\nReuse the method.', .65, 1.35, 8.4, 44, BG, bold=True)
    text(s, 'AI-assisted discovery → deterministic, auditable Python', .68, 4.42, 8.1, 21, 'B4D8D0')
    for i, (label, body) in enumerate([('01  OBSERVE', 'Readable baseline + exact errors'),
                                      ('02  EXPLAIN', 'Tools + competing hypotheses'),
                                      ('03  VERIFY', 'Experiments + regression checks')]):
        y = 1.65 + i*1.35
        rect(s, 9.15, y, 3.48, 1.12, '203D48')
        text(s, label, 9.35, y+.13, 3.08, 14, '8FD8C8', bold=True)
        text(s, body, 9.35, y+.48, 3.08, 18, BG)
    text(s, 'Team NAMA · USI Lugano', .68, 5.74, 10.9, 17, BG, bold=True)
    text(s, 'Mohammad Javad Amin · Nava Biglar · Malihe Ghasemian · Emad Aghajani', .68, 6.14, 11.9, 13, 'B4C6C8')

    s = slide('Turn each mismatch into an experiment.', 'Method / one loop across tasks', '0:15–0:35',
        'A dictionary-driven loader gives us consistent inputs. We write a baseline, then ask where, when and how it fails. Trees identify conditions; change-point and residual tools suggest conventions. We test alternatives and rerun dependent tasks before integrating a rule.',
        'Actual tools: legacy_loader.py, tools/rule_finder.py, tools/change_points.py, tools/residuals.py, tools/convention_search.py. The tree classifies mismatches; it does not establish the true formula. Convention search enumerates supplied candidate sets. Humans select features, propose candidates and assess evidence.',
        'Trace the loop left to right; emphasize testing rather than hypothesis generation alone.')
    steps = [('1  DECODE', 'Dictionary + history'), ('2  BASELINE', 'Readable formula'),
             ('3  EXPLAIN', 'Conditions + residuals'), ('4  TEST', 'Rank alternatives'), ('5  ENCODE', 'Exact Python')]
    for i,(head,body) in enumerate(steps):
        x=.64+i*2.46
        rect(s,x,2.10,2.27,1.45,'FFFFFF')
        text(s,head,x+.14,2.31,1.99,17,TEAL,bold=True)
        text(s,body,x+.14,2.85,1.99,17)
        if i<4: text(s,'→',x+2.28,2.57,.22,17,RED)
    line(s,11.75,3.81,11.75,4.13,TEAL)
    line(s,1.75,4.13,11.75,4.13,TEAL)
    text(s,'Repeat until the evidence supports the rule',3.2,4.35,7.0,22,TEAL,bold=True,align='center')
    card(s,.65,5.18,5.91,1.23,'AI + TEAM','Propose, explore, build tools',size=19)
    card(s,6.78,5.18,5.91,1.23,'VERIFICATION','Exact rows + intermediate checks',size=19)

    s = slide('Find where the system changed.', 'Example 1 / actual repository diagnostic', '0:35–0:58',
        'Applying newer conventions to older policies creates a strong historical pattern. Change-point analysis directs us to the conversion; we then test rounding, age and day-count candidates. The result is a dated rule with evidence. Both curves here show T4 training statements.',
        'Source: methodology_sample/era_evidence.csv. Red is the recorded T4 Neuron NG-only experiment from Plots/errors_by_era.csv. Teal is recalculated from the verified latest T4 snapshot and all 34,145 local training rows, with21 mismatches. This is local training evidence, not private accuracy or a fresh NG-only ablation of the final candidate. The annual plot motivates inspecting an era boundary; it does not independently identify the exact day. Current rules use conversion2007-08-11. Residual rates are small but not universally zero.',
        'Point to the older era, then to persistent errors after conversion. Explain carry-forward effects briefly.')
    with (OUT/'era_evidence.csv').open() as f:
        rows=[r for r in csv.reader(f)][1:]
    rows=[r for r in rows if r[1]]
    x0,y0,cw,ch=.98,2.55,7.3,3.02
    def xp(year): return x0+(year-1994)/(2025-1994)*cw
    def yp(value): return y0+ch-value/100*ch
    rect(s,x0,y0,xp(2007.61)-x0,ch,'E6E8E2')
    for tick in [0,25,50,75,100]:
        yy=yp(tick);line(s,x0,yy,x0+cw,yy,'CBD3D1',.7)
        text(s,str(tick)+'%',.46,yy-.10,.44,10,GRAY,align='right')
    for year in [1994,2000,2007,2013,2019,2025]:
        text(s,str(year),xp(year)-.24,y0+ch+.15,.53,11,GRAY,align='center')
    line(s,xp(2007.61),y0,xp(2007.61),y0+ch,GRAY,1)
    for col,color in [(1,RED),(2,TEAL)]:
        points=[(xp(int(r[0])),yp(float(r[col]))) for r in rows]
        for a,b in zip(points,points[1:]): line(s,*a,*b,color,2.8)
    text(s,'Share of wrong values (%)',.99,2.04,5.6,14,GRAY)
    text(s,'NG-only conventions / T4',1.0,6.04,3.9,14,RED,bold=True)
    text(s,'Current era-aware rules / T4',4.45,6.04,4.25,14,TEAL,bold=True)
    card(s,8.95,2.24,3.72,1.59,'CLUE','Errors cluster by historical era.',size=20)
    card(s,8.95,4.06,3.72,1.99,'EXPERIMENT','Test dated rounding, age and charge conventions.',size=20)
    text(s,'Local T4 training rows · NG-only: recorded era experiment · current: verified final snapshot',.99,6.55,11.4,10,GRAY)

    s = slide('Use the error shape to propose a formula.', 'Example 2 / clearly labelled illustrative arithmetic', '0:58–1:18',
        'Residuals also suggest formulas. This illustrative thirty-one-day charge is about three percent above a fixed monthly charge, suggesting actual-days over three-sixty. Our search tests competing day counts and rounding modes against real diagnostics. A plausible signature still needs exact validation.',
        'Illustration: value 10,000, annual rate 1%, elapsed period 31 days. Fixed month: 10,000×0.01/12=8.3333…; Actual/360: 10,000×0.01×31/360=8.6111…. Ratio of unrounded values=31/30=1.03333…. Displayed 8.33 and 8.61 use half-up cents for illustration; the historical era can use truncation. These are not observed policy outputs. Source tools: residuals.implied_ratios, convention_search.search, date_conventions.py.',
        'Point from the 1.033 ratio to the proposed day count; do not describe the toy amounts as measured outcomes.')
    text(s,'ILLUSTRATION  ·  value 10,000  ·  annual rate 1%  ·  period 31 days',.67,1.96,11.9,15,GRAY)
    card(s,.67,2.53,5.88,1.94,'CANDIDATE A · FIXED MONTH','10,000 × 1% ÷ 12\n8.33',accent=GRAY,size=27)
    card(s,6.78,2.53,5.88,1.94,'CANDIDATE B · ACTUAL/360','10,000 × 1% × 31 ÷ 360\n8.61',size=27)
    text(s,'Unrounded ratio: 31 / 30 = 1.0333…',.71,4.88,11.8,28,TEAL,bold=True)
    text(s,'Residual clue → candidate convention → exact comparison',.71,5.64,11.7,23,INK)
    text(s,'The search reuses the same engine; each task supplies its candidate choices and scoring function.',.71,6.25,11.7,15,GRAY)

    s = slide('Keep investigating when amounts are missing.', 'Example 3 / T7 transfers the method', '1:18–1:38',
        'For T7, we reused the workflow with weaker evidence. This actual Swiss example crosses the threshold between gross and net proceeds, supporting investigation of penalties. Booking presence constrains applicability; it cannot establish the amount. Public examples add checks, while hidden accuracy remains unresolved.',
        'Actual witness BL10002408/event 8, country CH, status E. research/t7_version2_experiments.md records gross tax-currency proceeds 5,042.28 and net 4,941.43; no VST booking. Latest cases.json confirms net CHF base 4,941.43 and no booked tax types. Policy currency is EUR, so label the displayed amounts CHF after conversion, not raw policy amounts. Booking absence supports applicability, not cent-exact tax amounts or remittance. Latest reported evaluated baseline: payout 1/20 and annual 15/20; current TRACE candidate has not been scored in this conversation.',
        'Use this as a generalization example; state the limitation in the same breath.')
    text(s,'Observed witness · BL10002408 / event 8 · Swiss tax residence',.67,1.96,11.9,15,GRAY)
    card(s,.67,2.52,3.85,1.82,'GROSS / CHF','5,042.28\nAbove 5,000',accent=GRAY,size=25)
    card(s,4.73,2.52,3.85,1.82,'NET / CHF','4,941.43\nBelow 5,000',size=25)
    card(s,8.79,2.52,3.85,1.82,'LEGACY EVIDENCE','No VST booking',size=24)
    text(s,'Supports a penalty/threshold hypothesis.',.72,4.84,11.8,27,TEAL,bold=True)
    text(s,'Booking presence constrains applicability. It cannot validate the amount or remittance date.',.72,5.58,11.7,21)
    text(s,'Sources: Version-2 investigation + current actual-data trace. T7 target amounts are unavailable locally.',.72,6.40,11.8,11,GRAY)

    s = slide('New target. Same investigative tools.', 'Generalization / what transfers', '1:38–1:55',
        'For another target, we supply new features, candidate formulas and evidence. We reuse the analysis, searches and validation process. Local T0-to-T4 scores exceed ninety-nine point seven percent. Our contribution is a reusable, human-guided method, with clear boundaries around verified results.',
        'Local train scores from the full regression: T0 225848/225858, T1 15028/15028, T2 3011/3019, T3 6137/6153, T4 34124/34145. These are not private results. T7 last reported evaluated versions 1/20 payout and 15/20 annual; latest TRACE overlay is unscored. Generality is demonstrated across targets within this challenge, not across arbitrary unseen industries. Decoder formats and relationship browsers require adapters. Maintainability latest local82.5, wall/RSS overhead documented in t7_trace.md.',
        'Close on the transfer argument. Supporting slides are skipped during the two-minute talk.')
    card(s,.67,2.08,5.88,2.31,'REUSE','Residual analysis\nTrees + change points\nCandidate search + exact checks',size=22)
    card(s,6.78,2.08,5.88,2.31,'ADAPT','Schema + relationships\nCandidate features and formulas\nReference evidence',accent=GRAY,size=22)
    text(s,'99.735–100%',.72,4.81,5.6,38,TEAL,bold=True)
    text(s,'Exact rows · T0–T4 · local training targets',.75,5.55,6.1,16,GRAY)
    text(s,'Human-guided discovery.\nEvidence-backed implementation.',7.20,4.98,5.25,24,INK,bold=True)
    text(s,'T7 evaluated baseline: payout 1/20; annual 15/20. Current TRACE candidate: organizer result pending.',.74,6.48,11.9,11,GRAY)

    s = slide('The reusable toolkit has explicit inputs.', 'Supporting slide / APIs and responsibilities', 'APPENDIX', '',
        'These are the current source APIs, not an invented autonomous agent architecture. Convention candidates and residual signatures include supplied insurance/date conventions, even though the search/ranking engine is reusable. LLMs accelerate development and hypothesis generation; exact comparison does not by itself prove unseen-data correctness.', appendix=True)
    rows=[('Rule finder','features + mismatch flags','Readable conditions to investigate'),
          ('Change points','dates + mismatch flags','Ranked historical boundaries'),
          ('Residuals','calculated + reference values','Rounding and ratio signatures'),
          ('Convention search','candidate options + score(choice)','Ranked candidate combinations'),
          ('Weak labels','predicted applicability + bookings','Agreement / disagreement cases')]
    for i,(name,inputs,outputs) in enumerate(rows):
        y=2.03+i*.78
        rect(s,.68,y,11.98,.66,'FFFFFF' if i%2==0 else LIGHT)
        text(s,name,.87,y+.15,2.47,17,TEAL,bold=True)
        text(s,inputs,3.50,y+.15,4.13,15)
        text(s,outputs,7.82,y+.15,4.50,15)
    text(s,'Stack: Python · pandas · scikit-learn · matplotlib · Decimal',.78,6.24,11.8,17,GRAY)

    s = slide('Keep local evidence separate from hidden scores.', 'Supporting slide / measured results and limits', 'APPENDIX', '',
        'Scores copied from .cache/t7-trace-rebase/after.log. Denominators include the observed local mismatches; do not assert all unlisted misses are confirmed manual corrections. T5 is a set of55 flags, not a measured hidden F1. T6 has29 regression checks, which do not constitute a jury score. Snapshot comparison covers 6,782,289 booking digests and22,393 unit histories. T7 current overlay changes7 stamp values, preserves6381 annual rows, and passes27 synthetic tests. MI82.5 versus updated-main82.9. Three-run median T7 wall23.720 vs23.633s; peak RSS1779.55 vs1779.02MiB.', appendix=True)
    rows=[('T0 Commission','225,848 / 225,858','99.9956%'),('T1 Due dates','15,028 / 15,028','100%'),
          ('T2 Maturity','3,011 / 3,019','99.7350%'),('T3 Surrender','6,137 / 6,153','99.7400%'),
          ('T4 Statement','34,124 / 34,145','99.9385%')]
    text(s,'LOCAL TRAINING TARGETS',.77,1.97,7.3,14,GRAY,bold=True)
    for i,(task,count,score) in enumerate(rows):
        y=2.44+i*.58
        text(s,task,.78,y,3.1,17)
        text(s,count,4.05,y,3.6,17)
        text(s,score,7.45,y,2.0,17,TEAL,bold=True)
    card(s,9.65,2.00,3.0,1.73,'MAINTAINABILITY','82.5\nLocal scorer',size=23)
    card(s,9.65,3.96,3.0,1.73,'REGRESSION','27 T7 tests\n29 T6 checks',size=21)
    text(s,'T5: 55 flags; hidden F1 unavailable. T7 evaluated baseline: 1/20 payout, 15/20 annual.',.78,5.81,11.75,16)
    text(s,'Latest TRACE overlay: seven stamp-only payout changes; all 6,381 annual rows unchanged vs updated main.',.78,6.30,11.75,14,GRAY)

    s = slide('Show what supported each decision.', 'Supporting slide / disclosure and evidence', 'APPENDIX', '',
        'AI usage: Claude Code and Codex assisted coding, experiments, review, documentation and presentation preparation. Team members set direction, selected candidate hypotheses and assessed results. Record actual usage accurately; the existing report records organizer clarification on coding-assistant use for T7, which should be retained only if the team can substantiate it. No language model is invoked by the submitted task entry points. Evidence sources: challenge PDFs; tools/*.py; Plots/errors_by_era.csv; research/t7_version2_experiments.md; research/t7_trace.md; local diagnostic JSON and verification logs. The slide4 calculation is explicitly illustrative. Freeze final metrics against the actual submitted code before recording.', appendix=True)
    card(s,.69,2.04,5.85,1.81,'OBSERVED','Training diagnostics, bookings, version history and organizer counts.',size=21)
    card(s,6.78,2.04,5.85,1.81,'ILLUSTRATIVE','The charge arithmetic example explains a signature; it is not a policy trace.',accent=GRAY,size=21)
    card(s,.69,4.08,5.85,2.16,'AI DISCLOSURE','Claude Code + Codex assisted investigation, coding and review. The team directs and evaluates.',size=21)
    card(s,6.78,4.08,5.85,2.16,'BOUNDARY','Reusable tools need new adapters and hypotheses. Hidden T7 accuracy remains unresolved.',accent=RED,size=21)


def render():
    matplotlib.rcParams.update({'font.family':FONT,'pdf.fonttype':42,'svg.fonttype':'none'})
    with PdfPages(OUT/'NAMA_Methodology_Sample.pdf') as pdf:
        for i,s in enumerate(SLIDES,1):
            fig=plt.figure(figsize=(W,H),facecolor='#'+(INK if s['dark'] else BG))
            ax=fig.add_axes([0,0,1,1]);ax.set(xlim=(0,W),ylim=(H,0));ax.axis('off')
            for o in s['items']:
                if o['kind']=='rect':
                    ax.add_patch(Rectangle((o['x'],o['y']),o['w'],o['h'],facecolor='#'+o['fill'],
                        edgecolor='#'+o['stroke'] if o['stroke'] else 'none',linewidth=.8))
                elif o['kind']=='line':
                    ax.plot([o['x'],o['x2']],[o['y'],o['y2']],color='#'+o['color'],linewidth=o['width'],solid_capstyle='butt')
                else:
                    xx=o['x'] + (o['w'] if o['align']=='right' else o['w']/2 if o['align']=='center' else 0)
                    ax.text(xx,o['y'],o['text'],fontfamily=FONT,fontsize=o['size'],fontweight='bold' if o['bold'] else 'normal',
                            color='#'+o['color'],ha=o['align'],va='top',linespacing=1.12)
            pdf.savefig(fig,facecolor=fig.get_facecolor())
            fig.savefig(OUT/f'slide_{i:02d}.png',dpi=120,facecolor=fig.get_facecolor())
            plt.close(fig)
    thumb=Image.new('RGB',(1200,3*247+42), '#E8ECE8')
    draw=ImageDraw.Draw(thumb)
    for i in range(len(SLIDES)):
        img=Image.open(OUT/f'slide_{i+1:02d}.png').convert('RGB')
        img.thumbnail((390,220))
        x=5+(i%3)*400;y=10+(i//3)*250
        thumb.paste(img,(x,y));draw.text((x,y+223),f'{i+1:02d} '+SLIDES[i]['tag'],fill='#142D39')
    thumb.save(OUT/'contact_sheet.png')


P='http://schemas.openxmlformats.org/presentationml/2006/main'
A='http://schemas.openxmlformats.org/drawingml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PR='http://schemas.openxmlformats.org/package/2006/relationships'
DECL='<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
NS=f'xmlns:a="{A}" xmlns:r="{R}" xmlns:p="{P}"'
GROUP='<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'


def emu(x): return round(x*914400)
def rels(rows):
    return DECL+f'<Relationships xmlns="{PR}">'+''.join(f'<Relationship Id="{i}" Type="{R}/{kind}" Target="{target}"/>' for i,kind,target in rows)+'</Relationships>'
def solid(c): return f'<a:solidFill><a:srgbClr val="{c}"/></a:solidFill>'
def shape_xml(o,n):
    name=escape(o.get('text',o['kind']).split('\n')[0][:80],{'"':'&quot;'})
    nv=f'<p:nvSpPr><p:cNvPr id="{n}" name="{name}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
    if o['kind']=='line':
        x,y=min(o['x'],o['x2']),min(o['y'],o['y2'])
        w,h=abs(o['x2']-o['x']),abs(o['y2']-o['y'])
        attrs=(' flipH="1"' if o['x2']<o['x'] else '')+(' flipV="1"' if o['y2']<o['y'] else '')
        return f'<p:sp>{nv}<p:spPr><a:xfrm{attrs}><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm><a:prstGeom prst="line"><a:avLst/></a:prstGeom><a:ln w="{round(o["width"]*12700)}">{solid(o["color"])}</a:ln></p:spPr></p:sp>'
    transform=f'<a:xfrm><a:off x="{emu(o["x"])}" y="{emu(o["y"])}"/><a:ext cx="{emu(o["w"])}" cy="{emu(o["h"])}"/></a:xfrm>'
    geom='<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
    if o['kind']=='rect':
        stroke=f'<a:ln>{solid(o["stroke"])}</a:ln>' if o.get('stroke') else '<a:ln><a:noFill/></a:ln>'
        return f'<p:sp>{nv}<p:spPr>{transform}{geom}{solid(o["fill"])}{stroke}</p:spPr></p:sp>'
    paragraphs=[]
    for t in o['text'].split('\n'):
        rpr=f'<a:rPr lang="en-US" sz="{o["size"]*100}" b="{int(o["bold"])}">{solid(o["color"])}<a:latin typeface="{FONT}"/><a:ea typeface="{FONT}"/><a:cs typeface="{FONT}"/></a:rPr>'
        paragraphs.append(f'<a:p><a:pPr algn="{dict(left="l",center="ctr",right="r")[o["align"]]}"><a:lnSpc><a:spcPct val="112000"/></a:lnSpc><a:spcAft><a:spcPts val="0"/></a:spcAft></a:pPr><a:r>{rpr}<a:t xml:space="preserve">{escape(t)}</a:t></a:r></a:p>')
    body='<p:txBody><a:bodyPr wrap="none" lIns="0" tIns="0" rIns="0" bIns="0" anchor="t"><a:noAutofit/></a:bodyPr><a:lstStyle/>'+''.join(paragraphs)+'</p:txBody>'
    return f'<p:sp>{nv}<p:spPr>{transform}{geom}<a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>{body}</p:sp>'


def notes_text(s):
    return f"{s['title']}\nTIME: {s['timing']}\n"+('SUPPORTING SLIDE — skipped in the two-minute presentation.\n' if s['appendix'] else '')+f"\nSAY:\n{s['say'] or 'Use only for follow-up questions.'}\n\nCUE:\n{s['cue']}\n\nSUPPORT / EVIDENCE (not spoken):\n{s['support']}"


def pptx():
    parts={}
    template=ROOT/'presentation/NAMA_Neuron_Migration.pptx'
    with zipfile.ZipFile(template) as z:
        parts['ppt/theme/theme1.xml']=z.read('ppt/theme/theme1.xml')
        master=z.read('ppt/notesMasters/notesMaster1.xml')
        template_notes=z.read('ppt/notesSlides/notesSlide1.xml')
    parts['ppt/notesMasters/notesMaster1.xml']=master
    parts['ppt/notesMasters/_rels/notesMaster1.xml.rels']=rels([('rId1','theme','../theme/theme1.xml')])
    color_map='<p:clrMap accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" bg1="lt1" bg2="lt2" folHlink="folHlink" hlink="hlink" tx1="dk1" tx2="dk2"/>'
    parts['ppt/slideMasters/slideMaster1.xml']=DECL+f'<p:sldMaster {NS}><p:cSld><p:spTree>{GROUP}</p:spTree></p:cSld>{color_map}<p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst><p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles></p:sldMaster>'
    parts['ppt/slideMasters/_rels/slideMaster1.xml.rels']=rels([('rId1','slideLayout','../slideLayouts/slideLayout1.xml'),('rId2','theme','../theme/theme1.xml')])
    parts['ppt/slideLayouts/slideLayout1.xml']=DECL+f'<p:sldLayout {NS} type="blank" preserve="1"><p:cSld name="Blank"><p:spTree>{GROUP}</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>'
    parts['ppt/slideLayouts/_rels/slideLayout1.xml.rels']=rels([('rId1','slideMaster','../slideMasters/slideMaster1.xml')])
    ids=''.join(f'<p:sldId id="{256+i}" r:id="rId{i+3}"/>' for i in range(1,len(SLIDES)+1))
    parts['ppt/presentation.xml']=DECL+f'<p:presentation {NS}><p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst><p:notesMasterIdLst><p:notesMasterId r:id="rId2"/></p:notesMasterIdLst><p:sldIdLst>{ids}</p:sldIdLst><p:sldSz cx="{emu(W)}" cy="{emu(H)}" type="screen16x9"/><p:notesSz cx="6858000" cy="9144000"/></p:presentation>'
    parts['ppt/_rels/presentation.xml.rels']=rels([('rId1','slideMaster','slideMasters/slideMaster1.xml'),('rId2','notesMaster','notesMasters/notesMaster1.xml'),('rId3','theme','theme/theme1.xml')]+[(f'rId{i+3}','slide',f'slides/slide{i}.xml') for i in range(1,len(SLIDES)+1)])
    for i,s in enumerate(SLIDES,1):
        bg=solid(INK if s['dark'] else BG)
        shapes=''.join(shape_xml(o,n) for n,o in enumerate(s['items'],2))
        show=' show="0"' if s['appendix'] else ''
        parts[f'ppt/slides/slide{i}.xml']=DECL+f'<p:sld {NS}{show}><p:cSld name="{escape(s["title"])}"><p:bg><p:bgPr>{bg}<a:effectLst/></p:bgPr></p:bg><p:spTree>{GROUP}{shapes}</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>'
        parts[f'ppt/slides/_rels/slide{i}.xml.rels']=rels([('rId1','slideLayout','../slideLayouts/slideLayout1.xml'),('rId2','notesSlide',f'../notesSlides/notesSlide{i}.xml')])
        root=ET.fromstring(template_notes)
        for sp in root.findall(f'.//{{{P}}}sp'):
            ph=sp.find(f'.//{{{P}}}ph')
            if ph is not None and ph.get('type')=='body':
                body=sp.find(f'{{{P}}}txBody')
                for node in list(body):
                    if node.tag==f'{{{A}}}p': body.remove(node)
                for value in notes_text(s).split('\n'):
                    p=ET.SubElement(body,f'{{{A}}}p');run=ET.SubElement(p,f'{{{A}}}r')
                    ET.SubElement(run,f'{{{A}}}t').text=value
        parts[f'ppt/notesSlides/notesSlide{i}.xml']=ET.tostring(root,encoding='utf-8',xml_declaration=True)
        parts[f'ppt/notesSlides/_rels/notesSlide{i}.xml.rels']=rels([('rId1','notesMaster','../notesMasters/notesMaster1.xml'),('rId2','slide',f'../slides/slide{i}.xml')])
    parts['_rels/.rels']=rels([('rId1','officeDocument','ppt/presentation.xml'),('rId2','metadata/core-properties','docProps/core.xml'),('rId3','extended-properties','docProps/app.xml')]).replace(R+'/metadata/core-properties','http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties')
    parts['docProps/core.xml']=DECL+'<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>NAMA — Methodology and Generalization</dc:title><dc:creator>Team NAMA</dc:creator><dc:description>Six-slide two-minute sample with three skipped supporting slides and presenter notes.</dc:description></cp:coreProperties>'
    parts['docProps/app.xml']=DECL+f'<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><Application>NAMA sample builder</Application><PresentationFormat>On-screen Show (16:9)</PresentationFormat><Slides>{len(SLIDES)}</Slides><Notes>{len(SLIDES)}</Notes></Properties>'
    types={'presentation':'application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml',
        'slide':'application/vnd.openxmlformats-officedocument.presentationml.slide+xml',
        'slideMaster':'application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml',
        'slideLayout':'application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml',
        'notesMaster':'application/vnd.openxmlformats-officedocument.presentationml.notesMaster+xml',
        'notesSlide':'application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml',
        'theme':'application/vnd.openxmlformats-officedocument.theme+xml'}
    ct=[]
    for name in parts:
        if name.endswith('.rels'):continue
        if name=='docProps/core.xml':mime='application/vnd.openxmlformats-package.core-properties+xml'
        elif name=='docProps/app.xml':mime='application/vnd.openxmlformats-officedocument.extended-properties+xml'
        else:
            folder=name.split('/')[1]
            key={'slides':'slide','notesSlides':'notesSlide','notesMasters':'notesMaster','slideMasters':'slideMaster','slideLayouts':'slideLayout'}.get(folder,'theme' if folder=='theme' else 'presentation')
            mime=types[key]
        ct.append(f'<Override PartName="/{name}" ContentType="{mime}"/>')
    parts['[Content_Types].xml']=DECL+'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'+''.join(ct)+'</Types>'
    for name,value in parts.items():
        ET.fromstring(value)
    with zipfile.ZipFile(OUT/'NAMA_Methodology_Sample.pptx','w',zipfile.ZIP_DEFLATED) as z:
        for name,value in parts.items(): z.writestr(name,value)


def documentation():
    main_words=sum(len(s['say'].split()) for s in SLIDES if not s['appendix'])
    assert main_words<=300,main_words
    md=['# NAMA methodology sample — presenter notes','',
        'Six main slides, planned duration 1:55. Three supporting slides are skipped in the slideshow.',
        f'Main narration: {main_words} words. Rehearse aloud; timing depends on delivery.',
        'Open the .key file in Keynote and choose View → Show Presenter Notes.',
        'Slides and notes are editable. The PPTX is an interchange copy; PDF is a viewing copy.',
        'The sample assumes the jury knows the challenge and opens directly with methodology.','']
    for i,s in enumerate(SLIDES,1):md += [f'## {i}. {s["title"]}', '',notes_text(s),'']
    md += ['## Source and measurement boundaries','',
        '- Chart: `era_evidence.csv`. NG-only is a stored experiment from `Plots/errors_by_era.csv`; current T4 is recomputed from the verified snapshot against all 34,145 training rows (21 mismatches). Neither is private accuracy.',
        '- Example 2 amounts are illustrative and explicitly labelled.',
        '- Example 3 CHF amounts come from the Version-2 investigation; the current actual-data trace confirms the net base and absent booking.',
        '- Local regression/MI/resource evidence: `research/t7_trace.md` and ignored `.cache/t7-trace-rebase/` logs.',
        '- T7 organizer counts describe evaluated baseline versions. The latest TRACE candidate has no reported organizer result.',
        '- Update the sample to the final submitted code and latest organizer results before recording.',
        '- AI assistance disclosed: Claude Code and Codex. Team decisions and validation remain human-guided.','']
    (OUT/'Presenter_Notes.md').write_text('\n'.join(md))
    (OUT/'notes').mkdir(exist_ok=True)
    for i,s in enumerate(SLIDES,1):
        (OUT/'notes'/f'slide_{i:02d}.txt').write_text(notes_text(s)+'\n')
    (OUT/'slide_model.json').write_text(json.dumps(SLIDES,indent=2,ensure_ascii=False)+'\n')
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'Plots/errors_by_era.csv',OUT/'era_evidence.csv',ROOT/'research/t7_version2_experiments.md',ROOT/'research/t7_trace.md']}
    (OUT/'build_manifest.json').write_text(json.dumps({'main_slides':6,'supporting_slides':3,'narration_words':main_words,'planned_seconds':115,'sources_sha256':hashes},indent=2)+'\n')
    print(f'Built {len(SLIDES)} slides; six-slide narration {main_words} words. Output: {OUT}')


if __name__=='__main__':
    build_content()
    render()
    pptx()
    documentation()
