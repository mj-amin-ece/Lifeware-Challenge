#!/bin/zsh
# Rebuild NAMA_presentation_120s.mp4: the deck as PDF -> 1920x1080 slides, Samantha (US English) reads
# video_narration.json, one clip per slide, laid on a timeline of exactly 120 seconds. macOS only (say, PDFKit, AVFoundation).
#   zsh presentation/video_build/build_video.sh path/to/deck.pdf
set -e
HERE=${0:A:h}; WORK=$(mktemp -d); mkdir -p $WORK/slides
swift $HERE/render.swift "$1" $WORK/slides
python3 - "$HERE/../video_narration.json" "$WORK" <<'PY'
import json, re, subprocess, sys
texts, work = json.load(open(sys.argv[1])), sys.argv[2]
durations = []
for i, text in enumerate(texts, 1):
    clip = f'{work}/seg_{i:02d}.aiff'
    subprocess.run(['say', '-v', 'Samantha', '-r', '150', '-o', clip, '--data-format=BEI16@44100', text], check=True)
    info = subprocess.run(['afinfo', clip], capture_output=True, text=True).stdout
    durations.append(float(re.search(r'estimated duration: ([\d.]+)', info).group(1)))
total, lead = 120.0, 0.4
gap = (total - sum(durations) - lead * len(durations)) / len(durations)
start, slides = 0.0, []
for i, spoken in enumerate(durations, 1):
    length = total - start if i == len(durations) else lead + spoken + gap
    slides.append({'image': f'slides/slide_{i:02d}.png', 'start': start, 'duration': length, 'audio': f'seg_{i:02d}.aiff', 'offset': lead})
    start += length
json.dump({'total': total, 'slides': slides}, open(f'{work}/timeline.json', 'w'))
PY
swift $HERE/assemble.swift $WORK $HERE/../NAMA_presentation_120s.mp4
