import { useEffect, useRef, useState } from "react";
import { Send, Eraser, Download, Bot, User } from "lucide-react";
import { api } from "../api";

interface Msg {
  role: string;
  content: string;
  ts: string;
}

const STORAGE_KEY = "chatbot-mcp-chat-history";
const PERSONALITY_KEY = "chatbot-mcp-chat-personality";

export function Chat() {
  const [msgs, setMsgs] = useState<Msg[]>(() => {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]"); }
    catch { return []; }
  });
  const [input, setInput] = useState("");
  const [persona, setPersona] = useState("");
  const [personas, setPersonas] = useState<any[]>([]);
  const [convId, setConvId] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [err, setErr] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [msgs]);

  useEffect(() => {
    api.personas.list().then((d) => setPersonas(d.personas || [])).catch(() => {});
    const saved = localStorage.getItem(PERSONALITY_KEY);
    if (saved) setPersona(saved);
  }, []);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(msgs.slice(-100)));
  }, [msgs]);

  const startConv = async () => {
    if (!persona) { setErr("Select a persona first"); return; }
    try {
      const conv = await api.conversations.create({ persona, platform: "web" });
      setConvId(conv.conversation_id);
      setMsg("system", `Started conversation with ${persona}`);
      setErr("");
    } catch (e: any) { setErr(String(e)); }
  };

  const setMsg = (role: string, content: string) => {
    setMsgs((prev) => [...prev, { role, content, ts: new Date().toISOString() }]);
  };

  const send = async () => {
    if (!input.trim() || sending) return;
    if (!convId) { setErr("Start a conversation first"); return; }
    const text = input;
    setInput("");
    setMsg("user", text);
    setSending(true);
    setErr("");
    try {
      const resp = await api.conversations.send(convId, text);
      setMsg("assistant", resp.response);
      if (resp.safety_verdict === "blocked") setErr("Message was blocked by safety rules");
    } catch (e: any) { setErr(String(e)); setMsg("assistant", "Error: " + String(e)); }
    finally { setSending(false); }
  };

  const clear = () => {
    setMsgs([]);
    setConvId(null);
    setErr("");
    localStorage.removeItem(STORAGE_KEY);
  };

  const exportChat = () => {
    const txt = msgs.map((m) => `[${m.ts.slice(0, 16)}] ${m.role}: ${m.content}`).join("\n\n");
    const blob = new Blob([txt], { type: "text/plain" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `chatbot-mcp-chat-${Date.now()}.txt`;
    a.click();
  };

  return (
    <div className="flex flex-col h-full max-w-3xl mx-auto" data-testid="chat-page">
      <div className="flex items-center gap-2 mb-4 flex-wrap" data-testid="chat-controls">
        <select
          className="bg-zinc-800 text-sm px-3 py-1.5 rounded-lg border border-zinc-700"
          value={persona}
          onChange={(e) => { setPersona(e.target.value); localStorage.setItem(PERSONALITY_KEY, e.target.value); }}
          data-testid="personality-select"
        >
          <option value="">Select persona...</option>
          {personas.map((p: any) => (
            <option key={p.name} value={p.name}>{p.display_name || p.name}</option>
          ))}
        </select>
        <button
          onClick={startConv}
          className="bg-amber-600 hover:bg-amber-500 text-sm px-3 py-1.5 rounded-lg disabled:opacity-50"
          disabled={!persona || !!convId}
        >
          {convId ? "Chatting" : "Start"}
        </button>
        <button onClick={exportChat} disabled={msgs.length === 0} data-testid="chat-export" className="text-zinc-500 hover:text-zinc-300 p-1.5 disabled:opacity-30">
          <Download className="w-4 h-4" />
        </button>
        <button onClick={clear} disabled={msgs.length === 0} data-testid="chat-clear" className="text-zinc-500 hover:text-zinc-300 p-1.5 disabled:opacity-30">
          <Eraser className="w-4 h-4" />
        </button>
        {err && <span className="text-red-400 text-xs ml-auto">{err}</span>}
      </div>

      <div className="flex-1 overflow-auto space-y-3 mb-4 pr-2" data-testid="chat-messages">
        {msgs.length === 0 && (
          <div className="text-center text-zinc-600 mt-16">
            <Bot className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p>Select a persona and start a conversation.</p>
          </div>
        )}
        {msgs.map((m, i) => (
          <div key={i} className={`flex gap-2 ${m.role === "user" ? "justify-end" : ""}`}>
            <div className={`max-w-[80%] p-3 rounded-xl text-sm ${
              m.role === "user" ? "bg-amber-600/20 border border-amber-600/30" : "bg-zinc-800 border border-zinc-700"
            }`}>
              <div className="flex items-center gap-1.5 mb-1 text-xs text-zinc-500">
                {m.role === "user" ? <User className="w-3 h-3" /> : <Bot className="w-3 h-3" />}
                {m.role}
              </div>
              <div className="whitespace-pre-wrap">{m.content}</div>
            </div>
          </div>
        ))}
        {sending && <div className="text-zinc-600 text-sm animate-pulse">Thinking...</div>}
        <div ref={bottomRef} />
      </div>

      <div className="flex gap-2">
        <input
          className="flex-1 bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-amber-500"
          placeholder="Type a message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          data-testid="chat-input"
        />
        <button
          onClick={send}
          disabled={sending || !input.trim()}
          data-testid="chat-send"
          className="bg-amber-600 hover:bg-amber-500 p-2 rounded-lg disabled:opacity-50"
        >
          <Send className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
}
