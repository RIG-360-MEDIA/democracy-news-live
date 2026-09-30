// Defensive reader-side filter: never render internal prompt / brief text as story copy (F9).
//
// Door B stories start life as an editor's topic brief ("Research the impact of the new tariff on
// Indian exporters"). If a draft is published before the generator replaced that brief with a real
// headline/dek — or a hand-authored story is saved with its working note — the instruction would reach
// readers verbatim. The reader mappers (manual-feed.ts) run every manual story through this and drop
// or blank anything that reads like an instruction to a model rather than journalism.
//
// Deliberately narrow: an imperative research verb followed by its object, an explicit "write a
// story/article …" instruction, a "Brief:/Prompt:/Instructions:" label, or model self-talk. A real
// headline such as "Research shows heat is cutting crop yields" does not match.

const PROMPT_PATTERNS: ReadonlyArray<RegExp> = [
  // "Research the impact of …", "Investigate how …", "Please analyse whether …"
  /^\s*(?:please\s+)?(?:research|investigate|analy[sz]e|examine|summari[sz]e|look\s+into|find\s+out(?:\s+about)?)\s+(?:the|how|why|whether|what|who|an?|recent|latest|current)\b/i,
  // "Write a 600-word article on …", "Draft an explainer about …", "Generate the story …"
  /\b(?:write|draft|generate|compose)\s+(?:an?|the|me\s+an?)\s+(?:\d+[-\s]word\s+)?(?:news\s+)?(?:article|story|piece|report|explainer|summary|headline|dek|brief)\b/i,
  // "Brief: …", "Prompt: …", "Instructions: …", "Task: …", "Topic brief: …"
  /^\s*(?:topic\s+)?(?:brief|prompt|instructions?|task|system\s+prompt)\s*:/i,
  // model self-talk
  /\bas an ai\b|\bas a language model\b/i,
];

/** True when `text` reads like an internal prompt/brief rather than publishable copy. */
export function isPromptLeak(text: string | null | undefined): boolean {
  if (!text) return false;
  return PROMPT_PATTERNS.some((re) => re.test(text));
}

/** `text` unless it is a prompt leak (→ null). */
export function withoutPromptLeak(text: string | null): string | null {
  return isPromptLeak(text) ? null : text;
}
