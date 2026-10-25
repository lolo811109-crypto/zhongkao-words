<div align="center">

<img src="docs/assets/banner.jpg" alt="Word Atlas: 7,298 IELTS words, each with its own illustration" width="100%">

# Word Atlas 词光

**One word, one picture. Light up your IELTS vocabulary.**<br>
7,298 core words · 14,596 original example sentences · 7,298 illustrations · UK & US audio · FSRS spaced repetition

[**Open the app →**](https://0xlei.tech/words/) &nbsp;·&nbsp; [▶ Launch film](docs/assets/launch.mp4) &nbsp;·&nbsp; [Download the dataset](data/) &nbsp;·&nbsp; [中文](README.md)

<a href="docs/assets/launch.mp4"><img src="docs/assets/launch-preview.webp" alt="Word Atlas launch film highlights" width="100%"></a>

<sub>▶ Click to watch the full 48-second launch film (with sound)</sub>

</div>

---

Word Atlas gives every word a picture, two sentences and a review rhythm that brings it back right before you forget. Every word you learn lights a star in your own word galaxy: 7,298 stars, one per word, rendered with custom WebGL2 shaders. It is free, needs no account, shows no ads and keeps your progress on your own device. The interface is in Chinese, built for Chinese-speaking IELTS learners; the dataset is useful to anyone.

Every definition, sentence, illustration and recording was made new for this project, paid for by the author, and released for free.

| | |
|---:|---|
| **7,298** | IELTS core entries, CEFR A1–C2, 19 topics |
| **7,298** | original illustrations |
| **14,596** | original example sentences with Chinese translations |
| **22,905** | audio clips: UK and US pronunciation, narrated examples |
| **0** | accounts, ads or trackers |

<p align="center"><a href="docs/assets/demo.mp4"><b>▶ Watch the 30-second app demo</b></a></p>

<img src="docs/assets/galaxy.jpg" alt="The word galaxy" width="100%">

<img src="docs/assets/today-desktop.jpg" alt="Today" width="100%">

## What every entry has

- **An illustration** in one consistent vintage field-guide style, showing the scene of the first example.
- **UK and US pronunciation**, plus a narrated everyday example (AI voices by ElevenLabs).
- **Two original examples**: a short everyday sentence and an IELTS-register sentence on a common exam topic, both with natural Chinese translations.
- **Up to three senses** in Chinese with short learner-friendly English definitions.
- **Collocations, word family, synonyms and antonyms**, and one usage tip.
- **CEFR level (A1–C2)** and one of **19 IELTS topics**.

## How it helps you remember

- **Active recall** with four question types: meaning, picture cloze, listening and spelling.
- **FSRS 6** spaced repetition (the open algorithm used by modern Anki) with an adjustable retention target.
- **Honest scoring**: only the first attempt counts; wrong words return in a different format within the session without inflating accuracy.
- **Typing studio** for words, sentences and dictation, measured separately from memory.
- **Share cards** for any word or for the day's session.

## The dataset (CC BY 4.0)

- [`data/word-atlas.json`](data/word-atlas.json) and [`data/word-atlas.csv`](data/word-atlas.csv)
- `public/atlas/img/` (512 px WebP) and `public/atlas/thumb/` (256 px)
- `public/atlas/audio/{uk,us,ex}/` MP3

Field reference: [docs/dataset.md](docs/dataset.md). Use it for Anki decks, apps, browser extensions, evaluation sets or research. Please credit "Word Atlas contributors".

## Run it

```bash
npm ci
npm run dev        # http://localhost:5188
npm test
npm run check:atlas
npm run build      # static site in dist/; ATLAS_BASE=/sub/path/ for sub-path hosting
```

## How the content was made

The headword list is a common IELTS reading core list (7,298 unique entries). All entry content is newly written for this project: definitions, examples, collocations and tips by a large language model under one lexicographic spec; illustrations by an image model in one art direction; audio by ElevenLabs. The pipeline lives in [`scripts/atlas/`](scripts/atlas) and is described in [docs/pipeline.md](docs/pipeline.md).

Everything passed automated structure and consistency checks, but it has **not** been proofread entry by entry. If you find a mistake, please open an issue or send a pull request against `data/`. This is not an official IELTS list and makes no score guarantees.

## License

Code: [MIT](LICENSE). Word content, illustrations and recordings: [CC BY 4.0](CONTENT_LICENSE.md), attribution "Word Atlas contributors".
