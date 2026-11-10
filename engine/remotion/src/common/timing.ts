// Shared timing + run-folder loading. The render's "public dir" IS the run folder
// (render.sh passes --public-dir runs/<niche>/<id>), so staticFile("plan.json") reads that run's plan.
import { staticFile } from "remotion";

export type Word = { word: string; start: number; end: number };
export type WordsFile = { duration: number; words: Word[] };
export type DataPoint = { date: string; value: number };
export type DataFile = { name: string; source: string; basis: string; resolution: string; series: DataPoint[] };

// Fields every style's plan.json shares (style-specific shot fields live in each style).
export type BasePlan<S extends { from: number; sfx?: string } = { from: number; sfx?: string }> = {
  version: 1;
  style: string;
  data?: Record<string, string>; // name -> file in the run, e.g. { "nvda": "data/nvda.json" }
  beds?: { sfx: string; volume: number }[]; // looping ambience under everything (vinyl, room tone)
  music?: { track: string; volume: number };
  endCard?: { text: string; seconds: number };
  tailSeconds?: number; // silence after the last word before the end card / end
  shots: S[];
};

export const FPS = 30;

export async function loadJson<T>(path: string): Promise<T> {
  const res = await fetch(staticFile(path));
  if (!res.ok) throw new Error(`Missing ${path} in the run folder`);
  return (await res.json()) as T;
}

// A shot starts at the first word it covers. The first shot starts at 0,
// each shot ends where the next begins, the last runs to the end.
export function shotStarts(fromWords: number[], words: Word[]): number[] {
  return fromWords.map((w, i) => {
    if (i === 0) return 0;
    if (w < 0 || w >= words.length) throw new Error(`Shot ${i}: word index ${w} out of range (0-${words.length - 1})`);
    return Math.max(0, words[w].start - 0.04);
  });
}

export const secToFrame = (s: number) => Math.round(s * FPS);

// Library files are copied into the run by render.sh, so the run renders on its own.
export const sfxFile = (name: string) => staticFile(`assets/sfx/${name}.wav`);
export const musicFile = (name: string) => staticFile(`assets/music/${name}.mp3`);
