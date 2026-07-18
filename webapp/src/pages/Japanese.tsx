import { useEffect, useState } from "react";
import { BookOpen, ExternalLink, Search, Library, FileText, List, Loader2 } from "lucide-react";

// Optional extra practice games — separate app, separate process. These are
// NOT required for the dictionary/kanji/vocab/quiz tools above, which are
// built into learnbot-mcp itself and always work.
const gamesAppUrl = "http://127.0.0.1:10987";
const gamesAppHealthUrl = "http://127.0.0.1:10987/health";

const gameLinks = [
  { href: `${gamesAppUrl}/games/japanese-language/kanji-master.html`, icon: BookOpen, label: "Kanji Master", desc: "Reading & meaning practice with spaced repetition" },
  { href: `${gamesAppUrl}/games/japanese-language/jlpt-practice-test.html`, icon: FileText, label: "JLPT Practice", desc: "Full N5-N1 format practice tests" },
  { href: `${gamesAppUrl}/games/japanese-language/jlpt-vocabulary.html`, icon: List, label: "JLPT Vocabulary", desc: "Master words by level" },
  { href: `${gamesAppUrl}/games/japanese-language/japanese-flashcards.html`, icon: Library, label: "Flashcards", desc: "SRS spaced repetition flashcard system" },
  { href: `${gamesAppUrl}/games/japanese-language/japanese-grammar.html`, icon: BookOpen, label: "Grammar", desc: "Pattern recognition grammar games" },
  { href: `${gamesAppUrl}/games/japanese-language/japanese-listening.html`, icon: BookOpen, label: "Listening", desc: "Web Speech API listening practice" },
  { href: `${gamesAppUrl}/games/japanese-language/kanji-table.html`, icon: Library, label: "Kanji Table", desc: "Full reference with stroke order & filters" },
  { href: `${gamesAppUrl}/games/educational/hiragana-katakana.html`, icon: BookOpen, label: "Hiragana/Katakana", desc: "Master both kana scripts" },
  { href: `${gamesAppUrl}/games/educational/karuta.html`, icon: BookOpen, label: "Karuta", desc: "Speed card matching game with AI opponent" },
  { href: `${gamesAppUrl}/games/educational/yojijukugo.html`, icon: BookOpen, label: "Yojijukugo", desc: "Four-character idiom quizzes" },
  { href: `${gamesAppUrl}/games/educational/vocabulary.html`, icon: Search, label: "Vocabulary Manager", desc: "Personal dictionary manager with JMdict" },
];

interface KanjiResult {
  kanji: string;
  meanings: string[];
  onyomi: string[];
  kunyomi: string[];
  jlpt: string;
  strokes: number;
}

interface VocabResult {
  expression?: string;
  japanese?: string;
  reading: string;
  translation?: string;
  meaning?: string;
  jlpt_level?: string;
}

export function Japanese() {
  const [mode, setMode] = useState<"kanji" | "vocab">("vocab");
  const [query, setQuery] = useState("");
  const [jlptFilter, setJlptFilter] = useState("");
  const [kanjiResults, setKanjiResults] = useState<KanjiResult[]>([]);
  const [vocabResults, setVocabResults] = useState<VocabResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [gamesAppOk, setGamesAppOk] = useState<boolean | null>(null);

  useEffect(() => {
    fetch(gamesAppHealthUrl, { signal: AbortSignal.timeout(3000) })
      .then((r) => setGamesAppOk(r.ok))
      .catch(() => setGamesAppOk(false));
  }, []);

  async function runSearch() {
    if (!query && !jlptFilter) return;
    setLoading(true);
    setError("");
    try {
      if (mode === "kanji") {
        const params = new URLSearchParams();
        if (query) params.set("q", query);
        if (jlptFilter) params.set("jlpt", jlptFilter);
        params.set("limit", "20");
        const r = await fetch(`/api/kanji/search?${params}`);
        const data = await r.json();
        if (!data.success) throw new Error(data.error || "Search failed");
        setKanjiResults(data.kanji);
        setVocabResults([]);
      } else {
        const params = new URLSearchParams();
        if (query) params.set("search", query);
        else if (jlptFilter) params.set("jlpt", jlptFilter);
        params.set("limit", "20");
        const r = await fetch(`/api/vocab/lookup?${params}`);
        const data = await r.json();
        if (!data.success) throw new Error(data.error || "Search failed");
        setVocabResults(data.vocab);
        setKanjiResults([]);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Search failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div data-testid="japanese-page">
      <h1 className="text-xl font-bold mb-2">Japanese Learning</h1>

      {/* Dictionary & kanji lookup — built into learnbot-mcp, always available */}
      <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-4 mb-6">
        <h2 className="text-sm font-semibold text-zinc-200 mb-3">
          Dictionary & Kanji Lookup
        </h2>
        <div className="flex gap-2 mb-3">
          <button
            onClick={() => setMode("vocab")}
            className={`px-3 py-1.5 rounded text-sm ${mode === "vocab" ? "bg-amber-600 text-white" : "bg-zinc-800 text-zinc-400"}`}
          >
            Vocabulary
          </button>
          <button
            onClick={() => setMode("kanji")}
            className={`px-3 py-1.5 rounded text-sm ${mode === "kanji" ? "bg-amber-600 text-white" : "bg-zinc-800 text-zinc-400"}`}
          >
            Kanji
          </button>
        </div>
        <div className="flex gap-2">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && runSearch()}
            placeholder={mode === "kanji" ? "Search kanji or meaning..." : "Search word, reading, or English..."}
            className="flex-1 bg-zinc-800 rounded px-3 py-1.5 text-sm text-zinc-100 border border-zinc-700"
          />
          <select
            value={jlptFilter}
            onChange={(e) => setJlptFilter(e.target.value)}
            className="bg-zinc-800 rounded px-2 py-1.5 text-sm text-zinc-100 border border-zinc-700"
          >
            <option value="">Any JLPT</option>
            {["N5", "N4", "N3", "N2", "N1"].map((l) => (
              <option key={l} value={l}>{l}</option>
            ))}
          </select>
          <button
            onClick={runSearch}
            disabled={loading}
            className="bg-amber-600 hover:bg-amber-500 text-white rounded px-3 py-1.5 text-sm flex items-center gap-1"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
          </button>
        </div>

        {error && <p className="text-red-400 text-sm mt-3">{error}</p>}

        {kanjiResults.length > 0 && (
          <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-2">
            {kanjiResults.map((k) => (
              <div key={k.kanji} className="bg-zinc-800 rounded p-2 text-center">
                <div className="text-2xl">{k.kanji}</div>
                <div className="text-xs text-zinc-400 mt-1">{k.meanings.join(", ")}</div>
                <div className="text-xs text-zinc-500">{k.jlpt} · {k.strokes} strokes</div>
              </div>
            ))}
          </div>
        )}

        {vocabResults.length > 0 && (
          <div className="mt-3 space-y-1.5">
            {vocabResults.map((v, i) => (
              <div key={i} className="bg-zinc-800 rounded p-2 flex justify-between items-center text-sm">
                <div>
                  <span className="text-zinc-100">{v.expression || v.japanese}</span>
                  <span className="text-zinc-500 ml-2">{v.reading}</span>
                </div>
                <div className="text-zinc-400 text-xs text-right max-w-[50%]">
                  {v.translation || v.meaning}
                  {v.jlpt_level && <span className="ml-2 text-amber-500">{v.jlpt_level}</span>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Extra practice games — separate app, optional */}
      <h2 className="text-sm font-semibold text-zinc-200 mb-1">Extra Practice Games</h2>
      <p className="text-zinc-500 text-xs mb-3">
        Optional — a separate app (games-app), not required for the dictionary/kanji lookup above.
      </p>
      {gamesAppOk === null && <p className="text-zinc-500 text-sm mb-4">Checking games-app...</p>}
      {gamesAppOk === false && (
        <p className="text-amber-500 text-sm mb-4">
          games-app not reachable on :10987. Start it from its own repo if you want these extra games —
          they're not needed for the dictionary/kanji lookup above.
        </p>
      )}
      {gamesAppOk === true && <p className="text-green-500 text-sm mb-4">games-app connected</p>}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {gameLinks.map(({ href, icon: Icon, label, desc }) => (
          <a
            key={href}
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-start gap-3 p-4 bg-zinc-900 rounded-lg border border-zinc-800 hover:border-zinc-700 transition-colors group"
          >
            <Icon className="w-5 h-5 mt-0.5 text-amber-500 shrink-0" />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1 text-sm font-medium text-zinc-200 group-hover:text-amber-500 transition-colors">
                {label}
                <ExternalLink className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
              <p className="text-xs text-zinc-500 mt-0.5">{desc}</p>
            </div>
          </a>
        ))}
      </div>
    </div>
  );
}
