# Lifeware Challenge - The Neuron Migration

Neural Wave AI Hackathon. Reverse-engineer the calculation rules of the legacy insurance system Neuron from its data
export, and write them as clear, deterministic Python code.

## Setup

The challenge data is not in this repository. Put the `legacy/` and `targets/` folders of the challenge next to
this README, then:

```
python3 -m venv .venv
.venv/bin/pip install -r starter_kit/my_solution/requirements.txt pandas pyarrow matplotlib nbformat nbclient ipykernel
```

## Data Processing

`starter_kit/my_solution/legacy_loader.py` reads every table of the export with one generic decoder driven by the
data dictionary `NRDICT`:

- `C` text: trimmed, `N(s)` numbers: `s` implied decimals, `D` dates: `CYYMMDD` (0 = no date, 9999999 = open end),
  `T` timestamps: `YYYYMMDDHHMMSS`.
- Decoded tables are cached as parquet in `.cache/` (NRBOOK: 12 s -> 0.1 s).
- `valid_on` picks the valid row of a versioned table on a date (highest version wins).

Data quality problems found while decoding:

- 10 impossible birth dates (e.g. 31 November), clamped to the month end and logged in `LegacyData.issues`.
- `NRCODE` rows have one text field, so the English text sits in `CD_TXTDE`.
- The smoker flag is `J/N`, not `Y/N`.

## Files

- `starter_kit/my_solution/submission.py`: the entry point with one function per task.
- `starter_kit/my_solution/legacy_loader.py`: loader and decoder of the legacy export.
- `starter_kit/my_solution/tools/policy_timeline.py`: prints all data of one policy and plots its timeline
  (`python tools/policy_timeline.py BL10000013`).
- `starter_kit/my_solution/notebooks/01_Data_Exploration.ipynb`: Data Processing, and a walk-through of policy
  `BL10000013` with the first rules found.
- `starter_kit/check.py`, `starter_kit/scoring.py`: local scoring from the organisers.
- `SCHEMA.md`: description of the export.

## Rules found so far

| Task | Rule |
|---|---|
| t0 | Commission = received premium x `NRCOMR` rate of the broker tier; returned and unpaid items are not counted |
| t1 | Collection on the next business day after the due date |
| t3 | Premiums of the first `PD_INIMON` months buy pot 1 units, later ones pot 2 |
| t4 | Entry charge rate taken on the premium's trade date; admin fee valid on the charge date |
