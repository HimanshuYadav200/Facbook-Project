// Shared timing helpers: turn word-indexed plans into frame-based timelines.
import { staticFile } from "remotion";

export type Word = { word: string; start: number; end: number };
export type WordsFile = { duration: number; words: Word[] };

export const FPS = 30;

export async function loadJson<T>(path: string): Promise<T> {
  const res = await fetch(staticFile(path));
  return (await res.json()) as T;
}

// A shot starts at the first word it covers. The first shot starts at 0,
// each shot ends where the next begins, the last runs to the end.
export function shotStarts(fromWords: number[], words: Word[]): number[] {
  return fromWords.map((w, i) => (i === 0 ? 0 : Math.max(0, words[Math.min(w, words.length - 1)].start - 0.04)));
}

export const secToFrame = (s: number) => Math.round(s * FPS);
