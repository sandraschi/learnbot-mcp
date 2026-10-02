import { useEffect, useState } from "react";
import { Volume2, Play, User, Users, AlertCircle } from "lucide-react";
import { api } from "../api";

export function Voices() {
  const [voices, setVoices] = useState<any[]>([]);
  const [testing, setTesting] = useState<string | null>(null);
  const [failed, setFailed] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/voices")
      .then((r) => r.json())
      .then((d) => setVoices(d.voices || []))
      .catch(() => {});
  }, []);

  const testVoice = async (id: string) => {
    setTesting(id);
    setFailed(null);
    try {
      const r = await fetch("/api/voice/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ voice_id: id, text: "Hello! This is a voice test." }),
      });
      const data = await r.json();
      if (!r.ok || !data.success) setFailed(id);
    } catch {
      setFailed(id);
    }
    setTesting(null);
  };

  const groups = [
    { label: "Female", key: "female", icon: User },
    { label: "Male", key: "male", icon: User },
    { label: "Neutral", key: "neutral", icon: Users },
  ];

  return (
    <div data-testid="voices-page">
      <h1 className="text-xl font-bold mb-2">Voices</h1>
      <p className="text-sm text-zinc-400 mb-4">
        Gemini TTS voices. Click the play button to hear a sample.
      </p>
      <div className="text-xs text-zinc-400 bg-zinc-900 border border-zinc-800 rounded-xl p-3 mb-6">
        <span className="font-medium text-zinc-300">Miko VR voice (locked Phase 3):</span>{" "}
        Gemini <span className="font-mono">Leda</span> speaks Miko&apos;s Japanese greeting
        (A/B sample: <span className="font-mono">docs/audio/miko-genki-gemini-leda.wav</span>).
        Kokoro <span className="font-mono">af_heart</span> is English-only — used for the
        English gloss, never the JP line. Qwen3-TTS needs a 3&nbsp;s clone reference
        before it can speak; VoiceStudio sidecar stays the local-first candidate
        once <span className="font-mono">:3900</span> is running.
      </div>

      {groups.map((group) => {
        const filtered = voices.filter((v) => v.gender === group.key);
        if (filtered.length === 0) return null;
        return (
          <div key={group.key} className="mb-6">
            <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3 flex items-center gap-2">
              <group.icon className="w-4 h-4" />
              {group.label}
            </h2>
            <div className="space-y-1">
              {filtered.map((v: any) => (
                <div
                  key={v.id}
                  className="flex items-center gap-3 bg-zinc-900 border border-zinc-800 rounded-xl p-3"
                >
                  <button
                    onClick={() => testVoice(v.id)}
                    disabled={testing === v.id}
                    title={failed === v.id ? "Voice test failed" : undefined}
                    className={`p-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 disabled:opacity-50 transition-colors ${
                      failed === v.id ? "text-red-400 hover:text-red-300" : "text-zinc-400 hover:text-amber-500"
                    }`}
                  >
                    {testing === v.id ? (
                      <Volume2 className="w-4 h-4 animate-pulse" />
                    ) : failed === v.id ? (
                      <AlertCircle className="w-4 h-4" />
                    ) : (
                      <Play className="w-4 h-4" />
                    )}
                  </button>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium">{v.id}</div>
                    <div className="text-xs text-zinc-400 truncate">
                      {failed === v.id ? <span className="text-red-400">Test failed &mdash; check TTS provider config</span> : v.desc}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
