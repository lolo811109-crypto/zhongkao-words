#!/usr/bin/env bash
# Galaxy music, effects and voice lines (ElevenLabs). Reads the key from $ATLAS_SECRETS/elevenlabs-2.key
# or $ELEVENLABS_API_KEY. Output: .local/forge/galaxy/. Pick takes, then run build_sfx.py.
set -euo pipefail
K="${ELEVENLABS_API_KEY:-$(tr -d '\n ' < "${ATLAS_SECRETS:-$HOME/.config/word-atlas}/elevenlabs-2.key")}"
OUT="$(dirname "$0")/../../.local/forge/galaxy"; mkdir -p "$OUT"; cd "$OUT"
API=https://api.elevenlabs.io/v1
for i in 0 1; do
  curl -sf -o "music-galaxy-$i.mp3" "$API/music?output_format=mp3_44100_128" -H "xi-api-key: $K" -H "Content-Type: application/json" \
    -d '{"prompt":"Calm ambient music for a study app galaxy view: slow evolving warm analog synth pads, soft celesta and music-box twinkles like stars, a gentle low drone, very sparse felt piano notes, no drums, no vocals, wondrous, peaceful, seamless and loop-friendly, consistent level","music_length_ms":120000,"model_id":"music_v1"}'
done
sfx() { curl -sf -o "$1.mp3" "$API/sound-generation?output_format=mp3_44100_128" -H "xi-api-key: $K" -H "Content-Type: application/json" \
  -d "{\"text\":\"$2\",\"duration_seconds\":$3,\"prompt_influence\":0.55,\"model_id\":\"eleven_text_to_sound_v2\"}"; }
for k in 0 1 2; do
  sfx "twinkle-$k" "One tiny delicate glass twinkle, a single soft high sparkle, very short and quiet" 0.5
  sfx "fly-$k" "A smooth airy whoosh flying through space with a soft shimmering tail, elegant, not aggressive" 1.4
  sfx "ignite-$k" "A star igniting: a soft warm bell ping with a gentle shimmering bloom, magical and calm" 1.3
done
say() { curl -sf -o "$1.mp3" "$API/text-to-speech/DowyQ68vDpgFYdWVGjc3?output_format=mp3_44100_128" -H "xi-api-key: $K" -H "Content-Type: application/json" \
  -d "{\"text\":\"[softly] $2\",\"model_id\":\"eleven_v3\",\"language_code\":\"zh\",\"voice_settings\":{\"stability\":0.5,\"similarity_boost\":0.8,\"style\":0.3}}"; }
for k in 0 1; do
  say "galaxy-hello-$k" "这是你的词汇星图。每学会一个词，就点亮一颗星。"
  say "galaxy-lit-$k" "今天的星星，已经点亮。"
done
