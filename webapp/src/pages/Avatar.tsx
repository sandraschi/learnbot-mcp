import { useState } from "react";
import { VRMViewer } from "../VRMViewer";
import { Bot } from "lucide-react";

export function Avatar() {
  const [persona, setPersona] = useState("miko");

  return (
    <div data-testid="avatar-page" className="max-w-lg mx-auto">
      <h1 className="text-xl font-bold mb-2">Avatar</h1>
      <p className="text-sm text-zinc-500 mb-6">
        3D VRM avatar viewer. Load a persona's avatar and watch it spin.
      </p>

      <div className="flex items-center gap-2 mb-6">
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

      <div className="flex justify-center">
        <VRMViewer size={360} persona={persona} />
      </div>

      <p className="text-xs text-zinc-600 text-center mt-4">
        The avatar loads from the persona's <code>avatar_vrm</code> path via the API.
        Uses three.js + @pixiv/three-vrm.
      </p>
    </div>
  );
}
