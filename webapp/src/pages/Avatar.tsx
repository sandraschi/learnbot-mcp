import { useState } from "react";
import { VRMViewer, VRM_EXPRESSIONS, type VrmExpression } from "../VRMViewer";
import { Bot, Eye, EyeOff, MessageCircle, RotateCw, Square } from "lucide-react";

export function Avatar() {
  const [persona, setPersona] = useState("miko");
  const [expression, setExpression] = useState<VrmExpression>("neutral");
  const [talking, setTalking] = useState(false);
  const [lookAtMouse, setLookAtMouse] = useState(true);
  const [autoRotate, setAutoRotate] = useState(true);

  const toggleClass = (active: boolean) =>
    `flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border transition-colors ${
      active
        ? "bg-amber-600 border-amber-500 text-white"
        : "bg-zinc-800 border-zinc-700 text-zinc-400 hover:border-zinc-500"
    }`;

  return (
    <div data-testid="avatar-page" className="max-w-lg mx-auto">
      <h1 className="text-xl font-bold mb-2">Avatar</h1>
      <p className="text-sm text-zinc-500 mb-6">
        Interactive VRM avatar. Drag to orbit, scroll to zoom, and drive her
        expressions below.
      </p>

      <div className="flex items-center gap-2 mb-4">
        <Bot className="w-4 h-4 text-zinc-500" />
        <input
          className="flex-1 bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-1.5 text-sm"
          value={persona}
          onChange={(e) => setPersona(e.target.value)}
          placeholder="Persona name"
        />
        <button
          onClick={() => setPersona(persona)}
          className="bg-amber-600 hover:bg-amber-500 text-sm px-3 py-1.5 rounded-lg"
        >
          Load
        </button>
      </div>

      <div className="flex justify-center mb-4">
        <VRMViewer
          size={360}
          persona={persona}
          expression={expression}
          talking={talking}
          lookAtMouse={lookAtMouse}
          autoRotate={autoRotate}
        />
      </div>

      <div className="mb-3">
        <div className="text-xs text-zinc-500 mb-1.5">Expression</div>
        <div className="flex flex-wrap gap-1.5">
          {VRM_EXPRESSIONS.map((name) => (
            <button
              key={name}
              onClick={() => setExpression(name)}
              className={toggleClass(expression === name)}
            >
              {name}
            </button>
          ))}
        </div>
      </div>

      <div className="mb-6">
        <div className="text-xs text-zinc-500 mb-1.5">Behaviour</div>
        <div className="flex flex-wrap gap-1.5">
          <button onClick={() => setTalking(!talking)} className={toggleClass(talking)}>
            {talking ? <Square className="w-3 h-3" /> : <MessageCircle className="w-3 h-3" />}
            {talking ? "stop talking" : "talk test"}
          </button>
          <button onClick={() => setLookAtMouse(!lookAtMouse)} className={toggleClass(lookAtMouse)}>
            {lookAtMouse ? <Eye className="w-3 h-3" /> : <EyeOff className="w-3 h-3" />}
            follow cursor
          </button>
          <button onClick={() => setAutoRotate(!autoRotate)} className={toggleClass(autoRotate)}>
            <RotateCw className="w-3 h-3" />
            auto-rotate
          </button>
        </div>
      </div>

      <p className="text-xs text-zinc-600 text-center mt-4">
        Drag = orbit, wheel = zoom. Auto-blink is always on. Expressions use VRM
        presets via three-vrm; the talk test cycles mouth visemes (real lip-sync
        from TTS phonemes is on the roadmap). Emotion tags from live chat will
        drive these same controls next.
      </p>
    </div>
  );
}
