/**
 * Per-repo chat prompt presets (learnbot-mcp: lessons with Miko).
 *
 * PRESET FILE CONTRACT (fleet template rule): this file is PER-REPO DATA.
 * Never vendor it — each repo writes its own presets for its own domain.
 * Shape: id/label/prompt. Selecting a preset fills the input box (replaces
 * when empty, appends otherwise); prompts end with an open cue.
 */

export interface ChatPreset {
  id: string;
  label: string;
  prompt: string;
}

export const CHAT_PRESETS: ChatPreset[] = [
  {
    id: "n5-quiz",
    label: "Quiz me (N5)",
    prompt:
      "Quiz me on N5 Japanese vocabulary. Ask one word at a time, wait for my answer, then tell me if I was right and give the reading plus one example sentence.\n\nStart with:\n",
  },
  {
    id: "grammar-check",
    label: "Check my sentence",
    prompt:
      "Check my Japanese sentence for grammar. Give the corrected version, explain what was wrong in plain terms, and state the JLPT level of the grammar point.\n\nMy sentence:\n",
  },
  {
    id: "lesson-starter",
    label: "Start a lesson",
    prompt:
      "Generate a beginner lesson for me. First ask which language and topic I want, then teach it step by step with a tiny quiz at the end.\n\nI want to learn:\n",
  },
  {
    id: "explain-ja",
    label: "Explain in Japanese",
    prompt:
      "Explain the following in simple Japanese (N4 level or easier), then give the English translation and the readings (furigana in parentheses) for any kanji.\n\nTEXT:\n",
  },
  {
    id: "roleplay",
    label: "Roleplay practice",
    prompt:
      "Roleplay with me in Japanese so I can practice a real situation. You play the other person, I play myself. Correct my mistakes gently as we go, and stay in character.\n\nSituation:\n",
  },
];
