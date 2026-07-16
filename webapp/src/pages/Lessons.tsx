import { useEffect, useState } from "react";
import { Plus, Trash2, BookOpen, Sparkles, Play } from "lucide-react";
import { api } from "../api";

interface Lesson {
  id: number;
  title: string;
  description: string;
  language: string;
  level: string;
  duration_min: number;
  tags: string[];
  sections: any[];
  vocab: any[];
  quiz: any[];
  created_at: string;
}

export function Lessons() {
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [selected, setSelected] = useState<Lesson | null>(null);
  const [err, setErr] = useState("");
  const [generating, setGenerating] = useState(false);
  const [genTitle, setGenTitle] = useState("");

  const load = async () => {
    try {
      const d: any = await api.lessons.list();
      setLessons(d.lessons || []);
    } catch {
      setErr("Failed to load lessons");
    }
  };
  useEffect(() => { load(); }, []);

  const generate = async () => {
    if (!genTitle.trim()) return;
    setGenerating(true);
    try {
      const r = await fetch("/api/lesson/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: genTitle, language: "ja", level: "N4" }),
      });
      const data = await r.json();
      if (data.success) {
        setGenTitle("");
        load();
      } else {
        setErr(data.error || "Generation failed");
      }
    } catch (e: any) {
      setErr(String(e));
    }
    setGenerating(false);
  };

  const remove = async (id: number) => {
    try {
      await fetch(`/api/lesson/${id}`, { method: "DELETE" });
      load();
    } catch (e: any) {
      setErr(String(e));
    }
  };

  return (
    <div data-testid="lessons-page">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold">Lessons</h1>
      </div>

      {err && <div className="text-red-400 text-sm mb-4">{err}</div>}

      {/* Generate section */}
      <div className="flex gap-2 mb-6">
        <input
          className="flex-1 bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm"
          placeholder="Lesson title to generate (e.g. 'Daily greetings')"
          value={genTitle}
          onChange={(e) => setGenTitle(e.target.value)}
        />
        <button
          onClick={generate}
          disabled={generating || !genTitle.trim()}
          className="flex items-center gap-1.5 bg-amber-600 hover:bg-amber-500 text-sm px-4 py-2 rounded-lg disabled:opacity-50"
        >
          <Sparkles className="w-4 h-4" />
          {generating ? "Generating..." : "Generate"}
        </button>
      </div>

      {/* Lesson grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {lessons.map((lesson) => (
          <div
            key={lesson.id}
            className="bg-zinc-900 border border-zinc-800 rounded-xl p-4"
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-amber-500 shrink-0" />
                <span className="font-medium text-sm">{lesson.title}</span>
              </div>
              <button
                onClick={() => remove(lesson.id)}
                className="text-zinc-600 hover:text-red-400 p-0.5"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
            {lesson.description && (
              <p className="text-xs text-zinc-500 mb-2 line-clamp-2">{lesson.description}</p>
            )}
            <div className="flex flex-wrap gap-1.5 text-xs text-zinc-600">
              <span className="bg-zinc-800 px-2 py-0.5 rounded">{lesson.level}</span>
              <span className="bg-zinc-800 px-2 py-0.5 rounded">{lesson.language}</span>
              <span className="bg-zinc-800 px-2 py-0.5 rounded">{lesson.duration_min}min</span>
              <span className="bg-zinc-800 px-2 py-0.5 rounded">{lesson.sections?.length || 0} sections</span>
              <span className="bg-zinc-800 px-2 py-0.5 rounded">{lesson.vocab?.length || 0} words</span>
            </div>
            {(lesson.tags?.length || 0) > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {lesson.tags.map((t: string, i: number) => (
                  <span key={i} className="text-xs text-zinc-600 bg-zinc-800/50 px-1.5 py-0.5 rounded">
                    #{t}
                  </span>
                ))}
              </div>
            )}
            <div className="flex gap-2 mt-3">
              <button
                onClick={() => setSelected(selected?.id === lesson.id ? null : lesson)}
                className="text-xs text-zinc-400 hover:text-zinc-200 underline"
              >
                {selected?.id === lesson.id ? "Hide" : "View"}
              </button>
              <button className="text-xs text-zinc-400 hover:text-amber-500 underline flex items-center gap-1">
                <Play className="w-3 h-3" /> Run
              </button>
            </div>

            {/* Expanded view */}
            {selected?.id === lesson.id && (
              <div className="mt-3 pt-3 border-t border-zinc-800 space-y-2 text-xs text-zinc-400 max-h-60 overflow-y-auto">
                {lesson.sections?.map((s: any, i: number) => (
                  <div key={i} className="p-2 bg-zinc-800/50 rounded">
                    <span className="text-amber-500 font-medium uppercase text-[10px]">{s.type}</span>
                    <p className="mt-0.5">{s.content?.slice(0, 200)}</p>
                  </div>
                ))}
                {lesson.vocab?.length > 0 && (
                  <div className="p-2 bg-zinc-800/50 rounded">
                    <span className="text-zinc-500 font-medium text-[10px] uppercase">Vocabulary</span>
                    {lesson.vocab.slice(0, 5).map((v: any, i: number) => (
                      <div key={i} className="flex gap-2 mt-1">
                        <span className="text-zinc-200">{v.word}</span>
                        <span className="text-zinc-600">{v.reading}</span>
                        <span className="text-zinc-500">{v.definition}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {lessons.length === 0 && !generating && (
        <div className="text-center text-zinc-600 py-12">
          <BookOpen className="w-10 h-10 mx-auto mb-3 opacity-30" />
          <p className="text-sm">No lessons yet. Generate one above.</p>
        </div>
      )}
    </div>
  );
}
