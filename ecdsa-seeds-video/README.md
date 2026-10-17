# It's Just Timestamps

An animated explainer (≈18 min, 1080p60) about Anthropic's October 16, 2026 finding
that Claude traced the origin of the NIST elliptic-curve seeds behind P-256 and its siblings.
The seeds were not hashes of a secret phrase. They were the output of the C library's
`lrand48`, seeded with Unix timestamps from 1997–98.

The film is for people in tech with no cryptography background. It builds up from zero:

| # | Chapter | What it teaches |
|---|---------|-----------------|
| – | Cold open | The mystery number, the bounty, "It's just timestamps." |
| 1 | A signature you can't copy | What digital signatures do, private vs public keys |
| 2 | Clock arithmetic | Modular arithmetic, one-way functions, discrete logs |
| 3 | Elliptic curves | Point addition, scalar multiplication, curves over finite fields, ECDLP |
| 4 | ECDSA | Signing, verifying, why it works, nonce reuse (PS3), biased nonces |
| 5 | Where do curves come from? | Weak curves, "verifiably random" seeds, Dual_EC, Solinas, the bounty |
| 6 | The investigation | Claude's PRNG scanner, the top-bit fingerprint, `lrand48` and its 17 hidden bits |
| 7 | Lattices | Truncated LCGs, lattice bases, LLL, recovering 40 hidden bits |
| 8 | Rewinding the clock | Running the LCG backwards to `srand48`, the timestamps, the reconstructed program, the base points |
| 9 | So, is ECDSA broken? | No: what it means, Valsorda's 30-bit estimate, what is still open, the bigger picture |

Everything on screen is computed from the real values: seeds, SHA-1 derivation of `b`, LCG states,
timestamps, FreeLIP base points, curve points. The narration script with sources is in
[`script.md`](script.md).

## Build

Requires Ubuntu 24.04-like tooling. `./setup.sh` installs ffmpeg, Cairo/Pango, a small TeX Live,
the Inter and JetBrains Mono fonts, and a Python venv at `/opt/manim-venv` with Manim CE 0.19.

```bash
./setup.sh
PY=/opt/manim-venv/bin/python

$PY build.py preview                  # 480p preview, no voice, captions burned in (~5 min)
```

### Adding the voiceover (OpenAI TTS)

```bash
export OPENAI_API_KEY=sk-...
$PY build.py voice                    # 75 clips via gpt-4o-mini-tts (voice "cedar") + whisper word timings
$PY build.py render -q h              # re-render all scenes at 1080p60, timed to the real clips
$PY build.py assemble -q h            # -> output/its_just_timestamps.mp4 (+ .srt)
# or all three at once:
$PY build.py all
```

Outputs land in `output/`: the MP4 (H.264 + AAC, soft English subtitle track), `its_just_timestamps.srt`,
and `chapters.txt` (YouTube-style chapter timestamps). A full 1080p60 render takes about 45 minutes on
4 cores. `-q p` (1440p60) and `-q k` (2160p60) also work and take proportionally longer.

- The cloud environment must allow `api.openai.com` (Network access → Allowed domains).
- `voice` caches clips by text, voice, model and instructions, so re-runs only synthesize what changed.
- Voice options: `--voice marin` (or any OpenAI voice), `TTS_MODEL=...`, `TTS_SPEED=0.95`, and
  `python tools/tts_openai.py --instructions-file my_style.txt` for a different delivery.
- Picture and voice are synchronised per segment *and* per word. Each `{mark}` in `script.md`
  is matched to the spoken word after it using whisper word timestamps. Visual beats land on
  that word, and the scenes stretch to the real clip lengths.

## How it fits together

```
script.md              narration: segments [id], sync marks {mark}, [[display|spoken]] pronunciations
scenes/common.py       palette, typography, icons, VOScene (segment timing, chapter cards, SFX cues)
scenes/s00…s09_*.py    one Manim scene per chapter
tools/narration.py     script parser; durations/marks from audio/timings.json or a speaking-rate estimate
tools/tts_openai.py    OpenAI TTS + whisper alignment -> audio/*.wav, audio/timings.json
tools/music.py         procedural ambient score and sound effects (no licensed audio)
tools/assemble.py      concat scenes, place clips on the timeline, duck the score, SRT, loudnorm -16 LUFS
tools/contact_sheet.py frame grids for reviewing renders
build.py               orchestration (parallel renders)
```

Each scene logs its actual segment start times to `build/timeline/<Scene>_<res>.json` while it
renders. The assembler places the audio from those frame-exact times, so sync never drifts.

## Sources

- Anthropic, "Claude reveals ECDSA curve origins", Oct 16, 2026, anthropic.com/research/ecdsa-curve-origins
- F. Valsorda, "The NIST Elliptic Curves Seeds Bounty Has Been Claimed", 2026, words.filippo.io/seeds-solved
- N. Koblitz, A. Menezes, "A Riddle Wrapped in an Enigma", 2015, eprint.iacr.org/2015/1018
- NIST FIPS 186-2 (2000); ANSI X9.62 (1999); seeds cross-checked against OpenSSL's built-in curve parameters
