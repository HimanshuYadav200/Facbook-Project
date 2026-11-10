// Style "explainer-fast": fast, excited explainer. A new picture every ~1.5-2 s, every shot moves (camera moves,
// 3D tilts and orbits, handheld wobble), cut-out characters ("actors") pop in and move over the scene,
// 1-3-word captions in the lower third, a whoosh on every shot change.
// Shot fields are documented in .claude/skills/style-explainer-fast/SKILL.md.
import React from "react";
import { AbsoluteFill, Easing, Img, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { AudioBed } from "../../common/AudioBed";
import { BasePlan, Word, shotStarts, secToFrame } from "../../common/timing";
import { Graphic, GraphicLayer, IN_SCENE, Sfx } from "./Graphics";

// x, y: the actor's feet (bottom centre) as shares of the frame; h: its height as a share of the frame height.
// at: word index when it enters (default: the shot's start).
type Actor = {
  img: string; x: number; y: number; h: number; flip?: boolean; at?: number;
  enter?: "pop" | "slideL" | "slideR" | "drop" | "none";
  idle?: "breathe" | "bob" | "wobble" | "hop" | "shake" | "lean" | "none";
};
type Shot = {
  from: number; img?: string; bg?: string; cam?: string; zoom?: number; focus?: [number, number];
  actors?: Actor[]; mg?: Graphic[]; hold?: number; fx?: ("flash" | "shake" | "punch")[]; sfx?: string; sfxVolume?: number; cutSfx?: string | null;
  captionY?: number;
};
export type ExplainerPlan = BasePlan<Shot> & { cutSfxVolume?: number; mgVolume?: number };
type Props = { words: Word[]; duration: number; plan: ExplainerPlan };

const FADE = 6; // 0.2 s dissolve between shots (reference: soft, quick)
const ease = Easing.out(Easing.cubic); // fast start, soft stop: the move "lands"

// Camera move per shot. t = 0..1 over the shot (eased). Returns a CSS transform for the scene layer.
// Scale stays >= ~1.2 so tilted and moved images still cover the whole frame.
function camera(cam: string, t: number, z: number, W: number, H: number): string {
  const lerp = (a: number, b: number) => a + (b - a) * t;
  switch (cam) {
    case "pushIn": return `scale(${z * lerp(1.12, 1.32)})`;
    case "pullOut": return `scale(${z * lerp(1.4, 1.15)})`;
    case "craneDown": return `translateY(${lerp(0.09, -0.07) * H}px) scale(${z * 1.3})`;
    case "craneUp": return `translateY(${lerp(-0.09, 0.07) * H}px) scale(${z * 1.3})`;
    case "panL": return `translateX(${lerp(0.1, -0.06) * W}px) scale(${z * 1.3})`;
    case "panR": return `translateX(${lerp(-0.1, 0.06) * W}px) scale(${z * 1.3})`;
    case "tiltDown": return `perspective(1400px) rotateX(${lerp(16, 0)}deg) translateY(${lerp(-0.05, 0) * H}px) scale(${z * lerp(1.4, 1.25)})`;
    case "tiltUp": return `perspective(1400px) rotateX(${lerp(-16, 0)}deg) translateY(${lerp(0.05, 0) * H}px) scale(${z * lerp(1.4, 1.25)})`;
    case "orbitL": return `perspective(1400px) rotateY(${lerp(-18, 2)}deg) translateX(${lerp(-0.06, 0) * W}px) scale(${z * 1.38})`;
    case "orbitR": return `perspective(1400px) rotateY(${lerp(18, -2)}deg) translateX(${lerp(0.06, 0) * W}px) scale(${z * 1.38})`;
    case "dive": return `perspective(1400px) rotateX(${lerp(22, 0)}deg) scale(${z * lerp(1.9, 1.2)})`;
    case "roll": return `rotate(${lerp(-7, 1)}deg) scale(${z * lerp(1.3, 1.38)})`;
    case "whip": return `translateX(${lerp(0.14, 0) * W}px) scale(${z * 1.32})`; // short slide + blur; a longer slide shows the image edge
    default: return `scale(${z * 1.2})`;
  }
}
export const CAMS = ["pushIn", "pullOut", "craneDown", "craneUp", "panL", "panR", "tiltDown", "tiltUp",
  "orbitL", "orbitR", "dive", "roll", "whip"];

// Handheld wobble: a few slow sine waves, so no shot is ever perfectly still.
function wobble(frame: number, seed: number) {
  const s = (f: number, p: number) => Math.sin(frame * f + seed * p);
  return `translate(${4 * s(0.13, 1.7) + 2 * s(0.31, 2.9)}px, ${3 * s(0.11, 4.1) + 2 * s(0.27, 0.6)}px) rotate(${0.35 * s(0.09, 3.3)}deg)`;
}

const ActorLayer: React.FC<{ a: Actor; enterFrame: number; seed: number }> = ({ a, enterFrame, seed }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const f = frame - enterFrame;
  if (f < 0) return null;
  const sp = spring({ frame: f, fps, config: { damping: 11, stiffness: 170, mass: 0.7 } }); // overshoots a little: lively
  let dx = 0, dy = 0, sc = 1, rot = 0, sy = 1;
  switch (a.enter ?? "pop") {
    case "pop": sc = sp; break;
    case "slideL": dx = (1 - sp) * -0.7 * width; break;
    case "slideR": dx = (1 - sp) * 0.7 * width; break;
    case "drop": dy = (1 - sp) * -0.6 * height; break;
  }
  const t = f / fps;
  switch (a.idle ?? "breathe") {
    case "breathe": sy *= 1 + 0.025 * Math.sin(t * 2 * Math.PI * 1.1 + seed); break;
    case "bob": dy += -0.012 * height * Math.abs(Math.sin(t * Math.PI * 2.2 + seed)); break;
    case "wobble": rot += 5 * Math.sin(t * 2 * Math.PI * 1.6 + seed); break;
    case "hop": dy += -0.04 * height * Math.max(0, Math.sin(t * 2 * Math.PI * 1.8 + seed)); sy *= 1 + 0.04 * Math.sin(t * 2 * Math.PI * 3.6); break;
    case "shake": dx += 7 * Math.sin(t * 90 + seed); rot += 1.5 * Math.sin(t * 70); break;
    case "lean": rot += interpolate(t, [0, 0.5], [0, 8], { extrapolateRight: "clamp", easing: ease }); break;
  }
  const h = a.h * height;
  return (
    <Img src={staticFile(`img/${a.img}`)} style={{
      position: "absolute", height: h, left: a.x * width, top: a.y * height - h,
      transform: `translateX(-50%) translate(${dx}px, ${dy}px) rotate(${rot}deg) scale(${sc}, ${sc * sy}) ${a.flip ? "scaleX(-1)" : ""}`,
      transformOrigin: "50% 100%", filter: "drop-shadow(0 10px 8px rgba(0,0,0,0.35))",
    }} />
  );
};

const ShotLayer: React.FC<{ s: Shot; i: number; len: number; fadeIn: boolean; startSec: number; words: Word[]; mgVol: number }> = ({ s, i, len, fadeIn, startSec, words, mgVol }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const t = interpolate(frame, [0, len + FADE], [0, 1], { extrapolateRight: "clamp", easing: ease });
  const cam = s.cam ?? CAMS[i % CAMS.length];
  const [fx, fy] = s.focus ?? [0.5, 0.5];
  const fxs = s.fx ?? [];
  // Whip: blurred for the first frames, like a fast pan. Punch: a quick zoom kick. Shake: a hit that settles.
  const blur = cam === "whip" ? interpolate(frame, [0, 8], [18, 0], { extrapolateRight: "clamp" }) : 0;
  const punch = fxs.includes("punch") ? 1 + 0.14 * Math.exp(-frame / 4) : 1;
  const k = fxs.includes("shake") ? 22 * Math.exp(-frame / 7) : 0;
  const shake = k ? `translate(${k * Math.sin(frame * 2.7)}px, ${k * Math.cos(frame * 3.3)}px)` : "";
  const opacity = fadeIn ? interpolate(frame, [0, FADE], [0, 1], { extrapolateRight: "clamp" }) : 1;
  const flash = fxs.includes("flash") ? interpolate(frame, [0, 2, 9], [0.9, 0.9, 0], { extrapolateRight: "clamp" }) : 0;
  // Frames into the shot when word `at` is spoken (actors and graphics enter on a word).
  const enterAt = (at?: number) => Math.round((at !== undefined && words[at] ? Math.max(0, words[at].start - startSec) : 0) * fps);
  const graphics = (inScene: boolean) => (s.mg ?? []).map((g, j) => IN_SCENE.has(g.type) === inScene
    ? <GraphicLayer key={j} g={g} enterFrame={enterAt(g.at)} seed={i * 13 + j} volume={mgVol} /> : null);
  return (
    <AbsoluteFill style={{ overflow: "hidden", opacity, background: "#111" }}>
      <AbsoluteFill style={{ transform: `${wobble(frame, i)} ${shake}` }}>
        {/* Scene + actors move together, so characters stay "in" the place while the camera moves. */}
        <AbsoluteFill style={{ transformOrigin: `${fx * 100}% ${fy * 100}%`, transform: `${camera(cam, t, (s.zoom ?? 1) * punch, width, height)}`, filter: blur ? `blur(${blur}px)` : undefined }}>
          {s.img
            ? <Img src={staticFile(`img/${s.img}`)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            : <AbsoluteFill style={{ background: `radial-gradient(circle at 50% 40%, ${s.bg} 0%, ${s.bg} 45%, rgba(0,0,0,0.35) 140%), ${s.bg}` }} />}
          {(s.actors ?? []).map((a, j) => <ActorLayer key={j} a={a} enterFrame={enterAt(a.at)} seed={i * 7 + j} />)}
          {graphics(true)}
        </AbsoluteFill>
        {/* Screen graphics: shake and wobble with the shot, but don't fly away with the camera move. */}
        {graphics(false)}
      </AbsoluteFill>
      {flash ? <AbsoluteFill style={{ background: "#fff", opacity: flash }} /> : null}
    </AbsoluteFill>
  );
};

// Words grouped into 1-3-word chunks: a chunk ends at punctuation, at 3 words, or at ~16 characters.
// Exported so the grouping can be checked in isolation.
export function chunks(words: Word[]): number[][] {
  const out: number[][] = [];
  let cur: number[] = [];
  words.forEach((w, i) => {
    cur.push(i);
    const chars = cur.reduce((n, j) => n + words[j].word.length + 1, 0);
    const next = words[i + 1];
    if (/[.?!,;:]["']?$/.test(w.word) || cur.length >= 3 || chars + (next ? next.word.length : 0) > 16) {
      out.push(cur);
      cur = [];
    }
  });
  if (cur.length) out.push(cur);
  return out;
}

const Caption: React.FC<{ words: Word[]; y: number }> = ({ words, y }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const groups = React.useMemo(() => chunks(words), [words]);
  let g = -1;
  for (let i = 0; i < groups.length; i++) {
    if (words[groups[i][0]].start <= t) g = i;
    else break;
  }
  if (g < 0) return null;
  const idx = groups[g];
  if (t > words[idx[idx.length - 1]].end + 0.5) return null; // hidden in long pauses
  const since = frame - Math.round(words[idx[0]].start * fps);
  const pop = spring({ frame: since, fps, config: { damping: 12, stiffness: 260, mass: 0.5 } });
  return (
    <div style={{ position: "absolute", top: `${y * 100}%`, left: "6%", right: "6%", textAlign: "center",
      transform: `translateY(-50%) scale(${0.8 + 0.2 * pop})` }}>
      <span style={{
        fontFamily: "'Arial Black', 'Arial Rounded MT Bold', Arial, sans-serif", fontSize: 84, color: "#fff",
        WebkitTextStroke: "14px #000", paintOrder: "stroke fill", lineHeight: 1.15,
        textShadow: "0 6px 10px rgba(0,0,0,0.6)",
      }}>{idx.map((j) => words[j].word).join(" ")}</span>
    </div>
  );
};

// One whoosh per shot change (a pool in sounds.json); the kind follows the move (dive = flying pass-by).
function cutSound(s: Shot): string | null {
  if (s.cutSfx !== undefined) return s.cutSfx;
  if (s.cam === "dive" || s.cam === "craneDown") return "dive";
  if (s.cam === "whip") return "whip";
  return "whoosh";
}

export const ExplainerFast: React.FC<Props> = ({ words, duration, plan }) => {
  const shots = plan.shots;
  // hold: the cut comes this many seconds after its word, so the previous shot's graphic can be read.
  const startSecs = shotStarts(shots.map((s) => s.from), words).map((t, i) => t + (shots[i].hold ?? 0));
  const starts = startSecs.map(secToFrame);
  const end = secToFrame(duration + (plan.tailSeconds ?? 0.6));
  const frame = useCurrentFrame();
  let cur = 0;
  starts.forEach((f, i) => { if (f <= frame) cur = i; });
  // Measured on the Eiffel run with the recorded sounds: whooshes ~9 dB and hits ~6-8 dB under the voice
  // (reference channel: 7-14 dB under).
  const cutVol = plan.cutSfxVolume ?? 0.22;
  return (
    <AbsoluteFill style={{ background: "#111" }}>
      {shots.map((s, i) => {
        const from = starts[i];
        const to = i + 1 < starts.length ? starts[i + 1] : end;
        const len = Math.max(1, to - from);
        const cut = i > 0 ? cutSound(s) : null;
        return (
          <Sequence key={i} from={from} durationInFrames={len + (i + 1 < shots.length ? FADE : 0)}>
            <ShotLayer s={s} i={i} len={len} fadeIn={i > 0} startSec={startSecs[i]} words={words} mgVol={plan.mgVolume ?? 0.35} />
            {cut ? <Sfx name={cut} seed={i} volume={cutVol} /> : null}
            {s.sfx ? <Sfx name={s.sfx} seed={i} volume={s.sfxVolume ?? 0.3} /> : null}
          </Sequence>
        );
      })}
      <AbsoluteFill style={{ pointerEvents: "none", background: "radial-gradient(ellipse at center, rgba(0,0,0,0) 60%, rgba(0,0,0,0.3) 100%)" }} />
      <Caption words={words} y={shots[cur].captionY ?? 0.7} />
      <AudioBed plan={plan} />
    </AbsoluteFill>
  );
};
