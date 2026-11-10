// Style "stickman-calm": calm narrated story over grey pencil-sketch stickman images.
// Slow camera move per shot, soft cross-dissolves, vignette, 2-line karaoke captions in the upper third.
// Shot fields are documented in .claude/skills/style-stickman-calm/SKILL.md.
import React from "react";
import { AbsoluteFill, Audio, Easing, Img, OffthreadVideo, Sequence, interpolate, random, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { AudioBed } from "../../common/AudioBed";
import { BasePlan, Word, sfxFile, shotStarts, secToFrame } from "../../common/timing";

// type "image" (still + camera move + blinks) or "clip" (an animated 5-8 s video, e.g. Meta AI animate, played as is).
// captionTop: caption height as a share of the frame (default 0.15), for close-ups where a head fills the top.
type Shot = {
  from: number; type?: "image" | "clip"; img?: string; clip?: string;
  motion?: string; zoom?: number; focus?: [number, number]; sfx?: string; captionTop?: number;
};
export type StickmanPlan = BasePlan<Shot>;
// Made by engine/tools/find_eyes.py: per image, each face's two eye centres and dot radius (shares of the image) + head grey.
export type Face = { eyes: [number, number][]; r: number; tone: number };
type Props = { words: Word[]; duration: number; plan: StickmanPlan; eyes?: Record<string, Face[]> };

const FADE = 12; // frames of cross-dissolve (0.4 s): the reference never hard-cuts
const YELLOW = "#FFD21F";

// Eyes shut for 4 frames (~0.13 s, a natural blink), every 2.8-4.5 s per face, starting 0.6-1.8 s into the shot.
const BLINK = 4;
function blinking(frame: number, fps: number, seed: string) {
  let at = Math.round((0.6 + 1.2 * random(seed + "a")) * fps);
  for (let k = 0; at <= frame; k++) {
    if (frame < at + BLINK) return true;
    at += Math.round((2.8 + 1.7 * random(`${seed}-${k}`)) * fps);
  }
  return false;
}

// Paints closed eyes over the open ones: a patch of head colour, then a short curved line.
const Blinks: React.FC<{ faces: Face[]; img: string }> = ({ faces, img }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  return (
    <svg viewBox={`0 0 ${width} ${height}`} style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}>
      {faces.map((f, i) => blinking(frame, fps, `${img}-${i}`) ? f.eyes.map(([x, y], j) => {
        const cx = x * width, cy = y * height, r = f.r * width;
        return (
          <g key={`${i}-${j}`}>
            <circle cx={cx} cy={cy} r={r * 1.7} fill={`rgb(${f.tone},${f.tone},${f.tone})`} />
            <path d={`M ${cx - r * 1.3} ${cy} Q ${cx} ${cy + r * 0.7} ${cx + r * 1.3} ${cy}`}
              stroke="#1d1d1d" strokeWidth={Math.max(2, r * 0.45)} fill="none" strokeLinecap="round" />
          </g>
        );
      }) : null)}
    </svg>
  );
};

const ImageShot: React.FC<{ s: Shot; len: number; fadeIn: boolean; faces: Face[] }> = ({ s, len, fadeIn, faces }) => {
  const frame = useCurrentFrame();
  // Slow and smooth: the whole move spans the shot plus its fade-out, eased at both ends.
  const t = interpolate(frame, [0, len + FADE], [0, 1], { extrapolateRight: "clamp", easing: Easing.inOut(Easing.sin) });
  const z = s.zoom ?? (s.type === "clip" ? 1 : 1.04);
  const [fx, fy] = s.focus ?? [0.5, 0.45];
  let scale = z, dx = 0, dy = 0;
  switch (s.motion ?? (s.type === "clip" ? "none" : "pushIn")) {
    case "pushIn": scale = z * (1 + 0.07 * t); break;
    case "pullOut": scale = z * (1.08 - 0.07 * t); break;
    case "panL": scale = z * 1.06; dx = 30 - 60 * t; break;
    case "panR": scale = z * 1.06; dx = -30 + 60 * t; break;
    case "panUp": scale = z * 1.06; dy = 40 - 80 * t; break;
    case "panDown": scale = z * 1.06; dy = -40 + 80 * t; break;
  }
  const opacity = fadeIn ? interpolate(frame, [0, FADE], [0, 1], { extrapolateRight: "clamp" }) : 1;
  return (
    <AbsoluteFill style={{ overflow: "hidden", opacity }}>
      {/* Image and blinks move together, so the closed eyes stay on the face during the camera move. */}
      <AbsoluteFill style={{ transformOrigin: `${fx * 100}% ${fy * 100}%`, transform: `translate(${dx}px, ${dy}px) scale(${scale})` }}>
        {s.type === "clip"
          ? <OffthreadVideo src={staticFile(`img/${s.clip}`)} muted style={{ width: "100%", height: "100%", objectFit: "cover" }} />
          : <Img src={staticFile(`img/${s.img}`)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />}
        {s.type !== "clip" && faces.length ? <Blinks faces={faces} img={s.img ?? ""} /> : null}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// Words grouped into short phrases (max 2 lines). A phrase ends at . ? ! always, at a comma once it has 3+ words,
// or at 7 words. Exported so the grouping can be checked in isolation.
export function phrases(words: Word[]): number[][] {
  const out: number[][] = [];
  let cur: number[] = [];
  words.forEach((w, i) => {
    cur.push(i);
    const chars = cur.reduce((n, j) => n + words[j].word.length + 1, 0);
    if (/[.?!]["']?$/.test(w.word) || (/,$/.test(w.word) && cur.length >= 3) || cur.length >= 7 || chars > 34) {
      out.push(cur);
      cur = [];
    }
  });
  if (cur.length) out.push(cur);
  return out;
}

const KaraokeCaption: React.FC<{ words: Word[]; top: number }> = ({ words, top }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const groups = React.useMemo(() => phrases(words), [words]);
  // The phrase whose first word has started most recently; hidden in long pauses after its last word.
  let g = -1;
  for (let i = 0; i < groups.length; i++) {
    if (words[groups[i][0]].start <= t) g = i;
    else break;
  }
  if (g < 0) return null;
  const idx = groups[g];
  if (t > words[idx[idx.length - 1]].end + 0.6) return null;
  const shown = idx.filter((j) => words[j].start <= t); // words appear as they are spoken
  const current = shown[shown.length - 1];
  return (
    <div style={{ position: "absolute", top: `${top * 100}%`, left: "9%", right: "9%", textAlign: "center", lineHeight: 1.18 }}>
      {shown.map((j) => (
        <span key={j} style={{
          fontFamily: "'Arial Rounded MT Bold', 'Helvetica Neue', Arial, sans-serif", fontSize: 62,
          color: j === current ? YELLOW : "#ffffff",
          textShadow: "0 0 6px rgba(0,0,0,0.85), 0 3px 4px rgba(0,0,0,0.9), 0 0 2px #000",
        }}>{words[j].word + " "}</span>
      ))}
    </div>
  );
};

export const StickmanCalm: React.FC<Props> = ({ words, duration, plan, eyes }) => {
  const shots = plan.shots;
  const starts = shotStarts(shots.map((s) => s.from), words).map(secToFrame);
  const end = secToFrame(duration + (plan.tailSeconds ?? 1.0));
  const frame = useCurrentFrame();
  let cur = 0; // shot on screen now (its caption position applies)
  starts.forEach((f, i) => { if (f <= frame) cur = i; });
  return (
    <AbsoluteFill style={{ background: "#e9e7e2" }}>
      {shots.map((s, i) => {
        const from = starts[i];
        const to = i + 1 < starts.length ? starts[i + 1] : end;
        const len = Math.max(1, to - from);
        // Each shot stays FADE frames longer, under the next shot fading in on top.
        return (
          <Sequence key={i} from={from} durationInFrames={len + (i + 1 < shots.length ? FADE : 0)}>
            <ImageShot s={s} len={len} fadeIn={i > 0} faces={(s.img && eyes?.[s.img]) || []} />
            {s.sfx ? <Audio src={sfxFile(s.sfx)} volume={0.12} /> : null}
          </Sequence>
        );
      })}
      <AbsoluteFill style={{ pointerEvents: "none", background: "radial-gradient(ellipse at center, rgba(0,0,0,0) 55%, rgba(0,0,0,0.38) 100%)" }} />
      <KaraokeCaption words={words} top={shots[cur].captionTop ?? 0.15} />
      <AudioBed plan={plan} />
    </AbsoluteFill>
  );
};
