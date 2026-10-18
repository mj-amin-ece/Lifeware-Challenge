# Methodology and generalization — sample presentation

Prepared for the two-minute video. The jury is assumed to know the challenge.
The slides open with our method and spend the presentation on tools, experiments,
examples, validation and transfer to another target.

- **NAMA_Methodology_Sample.key**: native editable Keynote presentation, with presenter notes.
- **NAMA_Methodology_Keynote_Export.pdf**: slides exported by Keynote.
- **NAMA_Methodology_With_Notes.pdf**: Keynote handout with presenter notes.
- **NAMA_Methodology_Sample.pptx**: editable interchange copy, including notes.
- **Presenter_Notes.md**: full narration, timing, delivery cues and evidence details.
- **contact_sheet.png**: quick overview of all nine slides.

Six main slides form the planned **1:55** presentation. The narration is **238
words**; rehearse aloud before recording. Slides 7–9 are supporting material and
are skipped during slideshow playback. In Keynote, choose **View → Show Presenter
Notes**. Keep the evidence explanations in the notes as preparation material;
only the text under `SAY` is the planned narration.

## Supporting examples

1. **Actual T4 era diagnostic:** a recorded NG-only experiment compared with
   current verified T4 training outputs. `era_evidence.csv` contains the plotted
   aggregate data. Current T4 has 21 mismatches over 34,145 target rows.
2. **Illustrative charge convention:** 31/360 versus 1/12 and the resulting
   1.0333 ratio. The amounts are explicitly illustrative, not observed outputs.
3. **Actual T7 witness:** gross versus net CHF amounts around a threshold, with
   no VST booking. Presence constrains applicability, not the tax amount.

Local T0–T4 scores are labelled as training results. Organizer T7 counts belong
to previously evaluated versions; no organizer score for the current TRACE
candidate is claimed. Update final measurements and organizer results against
the actual submitted code before recording.

The tools are reusable, human-guided components. Their usefulness across this
challenge does not establish automatic recovery of arbitrary business rules.
AI assistance includes Claude Code and Codex, as explained in the notes.

## Source and rebuilding

From the repository root:

```sh
env MPLCONFIGDIR=.cache/matplotlib .venv/bin/python presentation/build_methodology_sample.py
osascript presentation/convert_methodology_sample.applescript /absolute/path/to/presentation/methodology_sample
```

The generator uses the existing matplotlib/Pillow environment. The conversion
uses the locally installed Keynote application and macOS automation access.
`build_manifest.json` records the source hashes. Regeneration uses the Python
source and frozen aggregate chart data; direct edits made in Keynote are separate.
