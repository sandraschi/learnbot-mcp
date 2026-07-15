import { useEffect, useState } from "react";
import { Volume2, Play, User, Users } from "lucide-react";
import { api } from "../api";

export function Voices() {
  const [voices, setVoices] = useState<any[]>([]);
  const [testing, setTesting] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/voices")
      .then((r) => r.json())
      .then((d) => setVoices(d.voices || []))
      .catch(() => {});
  }, []);

  const testVoice = async (id: string) => {
    setTesting(id);
    try {
      await fetch("/api/voice/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ voice_id: id, text: "Hello! This is a voice test." }),
      });
    } catch {}
    setTimeout(() => setTesting(null), 2000);
  };

  const groups = [
    { label: "Female", key: "female", icon: User },
    { label: "Male", key: "male", icon: User },
    { label: "Neutral", key: "neutral", icon: Users },
  ];

  return (
    <div data-testid="voices-page">
      <h1 className="text-xl font-bold mb-2">Voices</h1>
      <p className="text-sm text-zinc-500 mb-6">
        Gemini TTS voices. Click the play button to hear a sample.
      </p>

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
                    className="p-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-400 hover:text-amber-500 disabled:opacity-50 transition-colors"
                  >
                    {testing === v.id ? (
                      <Volume2 className="w-4 h-4 animate-pulse" />
                    ) : (
                      <Play className="w-4 h-4" />
                    )}
                  </button>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium">{v.id}</div>
                    <div className="text-xs text-zinc-500 truncate">{v.desc}</div>
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
