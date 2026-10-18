# NAMA methodology sample — presenter notes

Six main slides, planned duration 1:55. Three supporting slides are skipped in the slideshow.
Main narration: 238 words. Rehearse aloud; timing depends on delivery.
Open the .key file in Keynote and choose View → Show Presenter Notes.
Slides and notes are editable. The PPTX is an interchange copy; PDF is a viewing copy.
The sample assumes the jury knows the challenge and opens directly with methodology.

## 1. Recover rules. Build evidence. Reuse the method.

Recover rules. Build evidence. Reuse the method.
TIME: 0:00–0:15

SAY:
Our approach is a reusable discovery loop. We start with a readable rule, use the mismatches to guide experiments, and turn supported findings into deterministic Python. AI helps investigate; exact comparisons decide what we keep.

CUE:
Face camera; then bring up the three-step stack.

SUPPORT / EVIDENCE (not spoken):
Opening goes directly to our approach: assume the jury knows the challenge. Assistants used in development include Claude Code and Codex; the submitted calculations are deterministic. This is a human-guided toolkit, not autonomous recovery of arbitrary formulas.

## 2. Turn each mismatch into an experiment.

Turn each mismatch into an experiment.
TIME: 0:15–0:35

SAY:
A dictionary-driven loader gives us consistent inputs. We write a baseline, then ask where, when and how it fails. Trees identify conditions; change-point and residual tools suggest conventions. We test alternatives and rerun dependent tasks before integrating a rule.

CUE:
Trace the loop left to right; emphasize testing rather than hypothesis generation alone.

SUPPORT / EVIDENCE (not spoken):
Actual tools: legacy_loader.py, tools/rule_finder.py, tools/change_points.py, tools/residuals.py, tools/convention_search.py. The tree classifies mismatches; it does not establish the true formula. Convention search enumerates supplied candidate sets. Humans select features, propose candidates and assess evidence.

## 3. Find where the system changed.

Find where the system changed.
TIME: 0:35–0:58

SAY:
Applying newer conventions to older policies creates a strong historical pattern. Change-point analysis directs us to the conversion; we then test rounding, age and day-count candidates. The result is a dated rule with evidence. Both curves here show T4 training statements.

CUE:
Point to the older era, then to persistent errors after conversion. Explain carry-forward effects briefly.

SUPPORT / EVIDENCE (not spoken):
Source: methodology_sample/era_evidence.csv. Red is the recorded T4 Neuron NG-only experiment from Plots/errors_by_era.csv. Teal is recalculated from the verified latest T4 snapshot and all 34,145 local training rows, with21 mismatches. This is local training evidence, not private accuracy or a fresh NG-only ablation of the final candidate. The annual plot motivates inspecting an era boundary; it does not independently identify the exact day. Current rules use conversion2007-08-11. Residual rates are small but not universally zero.

## 4. Use the error shape to propose a formula.

Use the error shape to propose a formula.
TIME: 0:58–1:18

SAY:
Residuals also suggest formulas. This illustrative thirty-one-day charge is about three percent above a fixed monthly charge, suggesting actual-days over three-sixty. Our search tests competing day counts and rounding modes against real diagnostics. A plausible signature still needs exact validation.

CUE:
Point from the 1.033 ratio to the proposed day count; do not describe the toy amounts as measured outcomes.

SUPPORT / EVIDENCE (not spoken):
Illustration: value 10,000, annual rate 1%, elapsed period 31 days. Fixed month: 10,000×0.01/12=8.3333…; Actual/360: 10,000×0.01×31/360=8.6111…. Ratio of unrounded values=31/30=1.03333…. Displayed 8.33 and 8.61 use half-up cents for illustration; the historical era can use truncation. These are not observed policy outputs. Source tools: residuals.implied_ratios, convention_search.search, date_conventions.py.

## 5. Keep investigating when amounts are missing.

Keep investigating when amounts are missing.
TIME: 1:18–1:38

SAY:
For T7, we reused the workflow with weaker evidence. This actual Swiss example crosses the threshold between gross and net proceeds, supporting investigation of penalties. Booking presence constrains applicability; it cannot establish the amount. Public examples add checks, while hidden accuracy remains unresolved.

CUE:
Use this as a generalization example; state the limitation in the same breath.

SUPPORT / EVIDENCE (not spoken):
Actual witness BL10002408/event 8, country CH, status E. research/t7_version2_experiments.md records gross tax-currency proceeds 5,042.28 and net 4,941.43; no VST booking. Latest cases.json confirms net CHF base 4,941.43 and no booked tax types. Policy currency is EUR, so label the displayed amounts CHF after conversion, not raw policy amounts. Booking absence supports applicability, not cent-exact tax amounts or remittance. Latest reported evaluated baseline: payout 1/20 and annual 15/20; current TRACE candidate has not been scored in this conversation.

## 6. New target. Same investigative tools.

New target. Same investigative tools.
TIME: 1:38–1:55

SAY:
For another target, we supply new features, candidate formulas and evidence. We reuse the analysis, searches and validation process. Local T0-to-T4 scores exceed ninety-nine point seven percent. Our contribution is a reusable, human-guided method, with clear boundaries around verified results.

CUE:
Close on the transfer argument. Supporting slides are skipped during the two-minute talk.

SUPPORT / EVIDENCE (not spoken):
Local train scores from the full regression: T0 225848/225858, T1 15028/15028, T2 3011/3019, T3 6137/6153, T4 34124/34145. These are not private results. T7 last reported evaluated versions 1/20 payout and 15/20 annual; latest TRACE overlay is unscored. Generality is demonstrated across targets within this challenge, not across arbitrary unseen industries. Decoder formats and relationship browsers require adapters. Maintainability latest local82.5, wall/RSS overhead documented in t7_trace.md.

## 7. The reusable toolkit has explicit inputs.

The reusable toolkit has explicit inputs.
TIME: APPENDIX
SUPPORTING SLIDE — skipped in the two-minute presentation.

SAY:
Use only for follow-up questions.

CUE:


SUPPORT / EVIDENCE (not spoken):
These are the current source APIs, not an invented autonomous agent architecture. Convention candidates and residual signatures include supplied insurance/date conventions, even though the search/ranking engine is reusable. LLMs accelerate development and hypothesis generation; exact comparison does not by itself prove unseen-data correctness.

## 8. Keep local evidence separate from hidden scores.

Keep local evidence separate from hidden scores.
TIME: APPENDIX
SUPPORTING SLIDE — skipped in the two-minute presentation.

SAY:
Use only for follow-up questions.

CUE:


SUPPORT / EVIDENCE (not spoken):
Scores copied from .cache/t7-trace-rebase/after.log. Denominators include the observed local mismatches; do not assert all unlisted misses are confirmed manual corrections. T5 is a set of55 flags, not a measured hidden F1. T6 has29 regression checks, which do not constitute a jury score. Snapshot comparison covers 6,782,289 booking digests and22,393 unit histories. T7 current overlay changes7 stamp values, preserves6381 annual rows, and passes27 synthetic tests. MI82.5 versus updated-main82.9. Three-run median T7 wall23.720 vs23.633s; peak RSS1779.55 vs1779.02MiB.

## 9. Show what supported each decision.

Show what supported each decision.
TIME: APPENDIX
SUPPORTING SLIDE — skipped in the two-minute presentation.

SAY:
Use only for follow-up questions.

CUE:


SUPPORT / EVIDENCE (not spoken):
AI usage: Claude Code and Codex assisted coding, experiments, review, documentation and presentation preparation. Team members set direction, selected candidate hypotheses and assessed results. Record actual usage accurately; the existing report records organizer clarification on coding-assistant use for T7, which should be retained only if the team can substantiate it. No language model is invoked by the submitted task entry points. Evidence sources: challenge PDFs; tools/*.py; Plots/errors_by_era.csv; research/t7_version2_experiments.md; research/t7_trace.md; local diagnostic JSON and verification logs. The slide4 calculation is explicitly illustrative. Freeze final metrics against the actual submitted code before recording.

## Source and measurement boundaries

- Chart: `era_evidence.csv`. NG-only is a stored experiment from `Plots/errors_by_era.csv`; current T4 is recomputed from the verified snapshot against all 34,145 training rows (21 mismatches). Neither is private accuracy.
- Example 2 amounts are illustrative and explicitly labelled.
- Example 3 CHF amounts come from the Version-2 investigation; the current actual-data trace confirms the net base and absent booking.
- Local regression/MI/resource evidence: `research/t7_trace.md` and ignored `.cache/t7-trace-rebase/` logs.
- T7 organizer counts describe evaluated baseline versions. The latest TRACE candidate has no reported organizer result.
- Update the sample to the final submitted code and latest organizer results before recording.
- AI assistance disclosed: Claude Code and Codex. Team decisions and validation remain human-guided.
