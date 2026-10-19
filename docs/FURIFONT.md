# Furifont Evaluation

Date: 2026-10-18
Source: https://furifont.antfu.me / https://github.com/antfu/furifont
Status: evaluated, not yet integrated
Canonical doc: `japanophile-mcp/docs/FURIFONT.md` (this file is the learnbot-specific companion)

## What it is

Furifont by Anthony Fu. A Japanese font that shows furigana by itself.
Plain text stays plain: no `<ruby>` markup, no JavaScript, no plugin.
Works anywhere custom fonts work.

```html
<p class="furifont">今日は日本語の勉強をします。</p>
<style>
.furifont {
  font-family: 'Furifont Sans';
  line-height: 1.7;
}
</style>
```

Compiled from Source Han Sans JP / Source Han Serif JP. Build step
draws dictionary readings into ligature glyphs (今日 -> one glyph with
きょう). Longer words win. Unknown kanji stays bare.

Releases ship Sans + Serif x Hiragana/Romaji, OTF + WOFF2, plus a
variable font ExtraLight-Heavy. Set `line-height >= 1.6`.

Licenses: code MIT, fonts OFL 1.1, dictionary CC BY-SA 4.0 (JMdict,
JMnedict, KANJIDIC2, JmdictFurigana, yomitan-jlpt-vocab, Tatoeba,
Japan Post, JR stations). Bundling allowed with attribution.

## Hard limitation

Upstream warning: a font sees one run of kanji at a time, not the
sentence around it, so readings can be wrong. Display layer only.
Never use for lesson grading, SM-2 quizzes, grammar check, or
dictionary lookup. Those stay on local SQLite (kanji, JMdict, JLPT
vocab) with no external service.

## Why it matters for learnbot-mcp

Learnbot renders Japanese in places where `<ruby>` is impossible:

- `/japanese` readers and AI-generated lesson passages (`source_lang` / `target_lang`)
- Chat transcripts and VRM avatar subtitles
- Discord / Resonite / Overte / VRChat bridges (chatbox prompts, classroom quiz loop)

One self-hosted WOFF2 + `.furifont` CSS class covers all of them.
Free Hiragana/Romaji toggle via the shipped variants.

## Integration recipe

1. Copy `Furifont Sans` WOFF2 into `webapp/public/fonts/` (self-host, no CDN). Mirror the CSS in the canonical doc:
   `.furifont { font-family: 'Furifont Sans', sans-serif; line-height: 1.7; }`
2. Add opt-in toggle on `/japanese` and lesson views. Label: `Reading aid - may be wrong`.
3. Optional: same toggle for Chat and `/vr` launchpad outputs.
4. Add attribution to Help page.
5. Keep grading/scoring paths on dictionary data, never on rendered glyphs.

## Future option

Custom JLPT-graded builds via `npx furifont build` (Node 22.18+,
`furifont.config.json`). N5-only furigana font for progressive
disclosure. Not started; coordinate with japanophile-mcp if pursued.

## Links

- Demo: https://furifont.antfu.me
- Repo: https://github.com/antfu/furifont
- HN discussion (2026-10-15, 336 pts, 67 comments): https://news.ycombinator.com/item?id=50100994
- Canonical evaluation: `japanophile-mcp/docs/FURIFONT.md`
