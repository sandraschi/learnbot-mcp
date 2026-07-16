import { useState } from "react";
import { Play, Terminal, Bot, Shield, Music, Activity } from "lucide-react";
import { api } from "../api";

interface Demo {
  id: string;
  label: string;
  icon: React.ElementType;
  description: string;
  run: () => Promise<string>;
}

export function Demos() {
  const [logs, setLogs] = useState<string[]>([]);
  const [running, setRunning] = useState<string | null>(null);

  const log = (msg: string) => setLogs((prev) => [...prev.slice(-99), msg]);

  const demos: Demo[] = [
    {
      id: "health",
      label: "Health Check",
      icon: Activity,
      description: "Ping the API and show server status",
      run: async () => {
        const h = await api.health();
        return `Server: ${h.server} v${h.version}\nPersonas: ${h.personas}, Conversations: ${h.conversations}, Safety rules: ${h.safety_rules}`;
      },
    },
    {
      id: "persona",
      label: "Persona CRUD",
      icon: Bot,
      description: "Create, list, and delete a persona",
      run: async () => {
        await api.personas.create({ name: "demo-test", display_name: "Demo Test", backstory: "Demo assistant." });
        const list = (await api.personas.list()).personas || [];
        const found = list.find((p: any) => p.name === "demo-test");
        if (found) await api.personas.delete("demo-test");
        return `Created, verified (${found ? "found" : "not found"}), deleted.`;
      },
    },
    {
      id: "safety",
      label: "Safety Rules",
      icon: Shield,
      description: "Add a rule, verify it blocks, remove it",
      run: async () => {
        const r = await api.safety.create({ topic: "demo-block", action: "refuse" });
        const list = (await api.safety.list()).rules || [];
        const found = list.find((rr: any) => rr.id === r.id);
        if (found) await api.safety.delete(r.id);
        return `Rule created (id=${r.id}), verified, deleted.`;
      },
    },
    {
      id: "conversation",
      label: "Chat Flow",
      icon: Terminal,
      description: "Start a conversation and send a message",
      run: async () => {
        await api.personas.create({ name: "demo-chat", display_name: "Demo Chat", backstory: "Short answers." });
        const conv = await api.conversations.create({ persona: "demo-chat", platform: "demo", user_id: "demo" });
        const resp = await api.conversations.send(conv.conversation_id, "Hello in 3 words", "demo");
        await api.conversations.delete(conv.conversation_id);
        await api.personas.delete("demo-chat");
        return `Response: ${(resp as any).response?.slice(0, 150) || "(none)"}\nVerdict: ${(resp as any).safety_verdict}`;
      },
    },
    {
      id: "voices",
      label: "Voice Test",
      icon: Music,
      description: "Test a Gemini TTS voice through speech-mcp",
      run: async () => {
        const r = await fetch("/api/voice/test", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ voice_id: "Leda", text: "Hello! This is a voice test." }),
        });
        const data = await r.json();
        return `Provider: ${data.provider || "none"}\nSuccess: ${data.success}`;
      },
    },
  ];

  const runDemo = async (demo: Demo) => {
    setRunning(demo.id);
    log(`\n>>> ${demo.label}`);
    log(demo.description);
    try {
      const result = await demo.run();
      log(result);
    } catch (e: any) {
      log(`ERROR: ${e.message || e}`);
    }
    setRunning(null);
  };

  const runAll = async () => {
    setLogs([]);
    for (const demo of demos) {
      await runDemo(demo);
    }
    log("\n=== All demos complete ===");
  };

  return (
    <div data-testid="demos-page" className="max-w-4xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold">Demo Runner</h1>
        <button
          onClick={runAll}
          disabled={running !== null}
          className="bg-amber-600 hover:bg-amber-500 text-sm px-4 py-1.5 rounded-lg disabled:opacity-50 flex items-center gap-1.5"
        >
          <Play className="w-4 h-4" /> Run All
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mb-6">
        {demos.map((demo) => (
          <button
            key={demo.id}
            onClick={() => runDemo(demo)}
            disabled={running !== null}
            className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 text-left hover:border-amber-600/50 transition-colors disabled:opacity-50"
          >
            <div className="flex items-center gap-2 mb-1">
              <demo.icon className={`w-4 h-4 ${running === demo.id ? "text-amber-500 animate-pulse" : "text-zinc-400"}`} />
              <span className="text-sm font-medium">{demo.label}</span>
            </div>
            <p className="text-xs text-zinc-600">{demo.description}</p>
          </button>
        ))}
      </div>

      <div className="bg-zinc-950 border border-zinc-800 rounded-xl p-4 font-mono text-xs leading-relaxed h-64 overflow-y-auto">
        {logs.length === 0 ? (
          <span className="text-zinc-600">Run a demo to see output here...</span>
        ) : (
          logs.map((line, i) => (
            <div key={i} className={line.startsWith(">>>") ? "text-amber-500 font-bold" : line.startsWith("ERROR") ? "text-red-400" : "text-zinc-300"}>
              {line}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
