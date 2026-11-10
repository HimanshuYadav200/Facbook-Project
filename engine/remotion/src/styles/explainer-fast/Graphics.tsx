// Motion graphics drawn over explainer-fast shots ("mg" in plan.json): stamps, labels, counters, arrows, money,
// speed lines, ?!, red X, circles, pointers. Same look as the flat-fastcut test: thick black outlines, springy
// entrances. No wobble of their own: they ride the shot's handheld wobble and shake, so the two never fight.
// Each graphic plays its own sound when it appears.
import React from "react";
import { AbsoluteFill, Audio, Easing, Sequence, interpolate, random, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { BigArrow, Money, SpeedLines } from "../flat-fastcut/Props";
import { sfxFile } from "../../common/timing";
import SOUNDS from "./sounds.json";

// A pool name ("whoosh") or an exact file ("whoosh_r3") -> one file + its volume. seed picks the variant,
// so neighbouring cuts/graphics sound different but every re-render sounds the same.
export function pickSound(name: string, seed: number, volume: number): { src: string; volume: number } {
  const pool = (SOUNDS.pools as Record<string, string[]>)[name];
  const file = pool ? pool[Math.abs(seed) % pool.length] : name;
  return { src: sfxFile(file), volume: volume * ((SOUNDS.gain as Record<string, number>)[file] ?? 1) };
}
export const Sfx: React.FC<{ name: string; seed: number; volume: number }> = ({ name, seed, volume }) => {
  const s = pickSound(name, seed, volume);
  return <Audio src={s.src} volume={s.volume} />;
};

// x, y: centre (pointer: the tip) as shares of the frame; size: width as a share of the frame width;
// at: word index when it appears (default: shot start); sfx: override the default sound (null = none).
export type Graphic = {
  type: "stamp" | "label" | "counter" | "arrow" | "money" | "speedLines" | "marks" | "cross" | "circle" | "pointer";
  x?: number; y?: number; size?: number; at?: number; text?: string; to?: number; dir?: string; rot?: number;
  sfx?: string | null;
};

// Default sound per graphic: pool names from sounds.json.
const SOUND: Record<Graphic["type"], string | null> = {
  stamp: "stamp", label: "pop", counter: "tick", arrow: "whip", money: "cash", speedLines: null,
  marks: "boing", cross: "thud", circle: "slide", pointer: "pop",
};
const SIZE: Record<Graphic["type"], number> = {
  stamp: 0.62, label: 0.5, counter: 0.8, arrow: 0.3, money: 0.26, speedLines: 1, marks: 0.3, cross: 0.4, circle: 0.45, pointer: 0.28,
};
// These mark something in the picture, so they move with the camera; the rest sit on the screen.
export const IN_SCENE = new Set(["cross", "circle", "pointer"]);

const INK = "#111";
const RED = "#e23b3b";
const FONT = "'Arial Black', 'Arial Rounded MT Bold', Arial, sans-serif";
const COUNT_FRAMES = 24; // counters run 0.8 s, then land with a ding
const ease = Easing.out(Easing.cubic);

// Font size so `text` fills about `w` px (Arial Black capitals are ~0.75 em wide).
const fit = (text: string, w: number, max: number) => Math.min(max, w / (0.75 * Math.max(3, text.length)));

const Body: React.FC<{ g: Graphic; seed: number }> = ({ g, seed }) => {
  const f = useCurrentFrame();
  const { fps, width: W, height: H } = useVideoConfig();
  const w = (g.size ?? SIZE[g.type]) * W;
  const x = (g.x ?? 0.5) * W, y = (g.y ?? 0.3) * H;
  const pop = spring({ frame: f, fps, config: { damping: 9, stiffness: 260, mass: 0.6 } }); // overshoots: lively
  const at = (inner: React.ReactNode, transform = "") => (
    <div style={{ position: "absolute", left: x, top: y, transform: `translate(-50%, -50%) ${transform}` }}>
      {inner}
    </div>
  );
  const text = (g.text ?? "").toUpperCase();

  switch (g.type) {
    case "stamp": {
      // Slams down from big to normal, slightly rotated, like a rubber stamp.
      const s = spring({ frame: f, fps, config: { damping: 15, stiffness: 320, mass: 0.6 } });
      return at(
        <div style={{ fontFamily: FONT, fontSize: fit(text, w, 170), color: RED, border: `14px solid ${RED}`, borderRadius: 18,
          padding: "6px 28px", background: "rgba(255,248,235,0.88)", whiteSpace: "nowrap", lineHeight: 1.1,
          boxShadow: "0 10px 24px rgba(0,0,0,0.45)" }}>{text}</div>,
        `rotate(${g.rot ?? -12}deg) scale(${interpolate(s, [0, 1], [2.6, 1])})`,
      );
    }
    case "label":
      return at(
        <div style={{ fontFamily: FONT, fontSize: fit(text, w, 120), color: INK, background: "#fff7d6", border: `10px solid ${INK}`,
          borderRadius: 22, padding: "8px 30px", whiteSpace: "nowrap", lineHeight: 1.15, boxShadow: "0 10px 20px rgba(0,0,0,0.4)" }}>{text}</div>,
        `rotate(${g.rot ?? -4}deg) scale(${0.4 + 0.6 * pop})`,
      );
    case "counter": {
      const p = interpolate(f, [0, COUNT_FRAMES], [0, 1], { extrapolateRight: "clamp", easing: ease });
      const n = Math.round((g.to ?? 0) * p).toLocaleString("en-US");
      const land = f >= COUNT_FRAMES ? 1 + 0.18 * Math.exp(-(f - COUNT_FRAMES) / 4) : 1;
      const style = { fontFamily: FONT, color: "#ffd23f", WebkitTextStroke: `16px ${INK}`, paintOrder: "stroke fill" as const,
        textShadow: "0 8px 16px rgba(0,0,0,0.55)", lineHeight: 1.0, textAlign: "center" as const, whiteSpace: "nowrap" as const };
      const full = (g.to ?? 0).toLocaleString("en-US");
      return at(
        <div style={style}>
          <div style={{ fontSize: fit(full, w, 230) }}>{n}</div>
          {text ? <div style={{ fontSize: fit(text, w * 0.8, 110), color: "#fff" }}>{text}</div> : null}
        </div>,
        `scale(${(0.5 + 0.5 * pop) * land})`,
      );
    }
    case "arrow": {
      const down = g.dir === "down";
      const enter = (1 - pop) * (down ? -0.5 : 0.5) * H;
      return at(<div style={{ width: w, height: w * 4 / 3 }}><BigArrow dir={down ? "down" : "up"} /></div>, `translateY(${enter}px)`);
    }
    case "money": {
      // Bills tumbling down the frame (rain) or flying across it (left/right).
      const bills = Array.from({ length: 9 }, (_, i) => {
        const r = (k: string) => random(`m${seed}-${i}-${k}`);
        const speed = 34 + r("s") * 22;
        let bx: number, by: number;
        if (g.dir === "left" || g.dir === "right") {
          const run = ((f * speed * 1.4 + r("o") * (W + 600)) % (W + 600)) - 300;
          bx = g.dir === "right" ? run : W - run;
          by = (0.15 + r("y") * 0.55) * H + 40 * Math.sin(f / 5 + i);
        } else {
          bx = r("x") * W;
          by = ((f * speed + r("o") * (H + 600)) % (H + 600)) - 300;
        }
        const rot = 40 * Math.sin(f / (6 + r("r") * 6) + i);
        return (
          <div key={i} style={{ position: "absolute", left: bx, top: by, width: w, height: w, transform: `translate(-50%, -50%) rotate(${rot}deg) scaleY(${Math.cos(f / 7 + i)})` }}>
            <Money count={1} />
          </div>
        );
      });
      return <AbsoluteFill style={{ opacity: Math.min(1, f / 4) }}>{bills}</AbsoluteFill>;
    }
    case "speedLines":
      return <AbsoluteFill style={{ opacity: 0.85 }}><SpeedLines frame={f} /></AbsoluteFill>;
    case "marks":
      return at(
        <div style={{ fontFamily: FONT, fontSize: w, color: "#ffd23f", WebkitTextStroke: `14px ${INK}`, paintOrder: "stroke fill",
          lineHeight: 1, textShadow: "0 8px 14px rgba(0,0,0,0.5)" }}>{g.text || "?!"}</div>,
        `rotate(-6deg) scale(${pop})`,
      );
    case "cross": {
      // Two thick red strokes drawn one after the other.
      const a = interpolate(f, [0, 5], [1, 0], { extrapolateRight: "clamp" });
      const b = interpolate(f, [4, 9], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
      const line = (d: string, off: number) => <path d={d} pathLength={1} strokeDasharray={1} strokeDashoffset={off} />;
      return at(
        <svg width={w} height={w} viewBox="0 0 100 100" style={{ overflow: "visible" }}>
          <g fill="none" strokeLinecap="round">
            <g stroke={INK} strokeWidth={22}>{line("M12 12 L88 88", a)}{line("M88 12 L12 88", b)}</g>
            <g stroke={RED} strokeWidth={14}>{line("M12 12 L88 88", a)}{line("M88 12 L12 88", b)}</g>
          </g>
        </svg>,
      );
    }
    case "circle": {
      // A hand-drawn loop around something, drawn on in 8 frames (slightly more than one turn, like a marker).
      const off = interpolate(f, [0, 8], [1, 0], { extrapolateRight: "clamp" });
      const d = "M60 8 C92 6 116 26 114 52 C112 80 84 96 56 94 C24 92 4 72 6 48 C8 22 34 6 66 10";
      return at(
        <svg width={w} height={w * 0.8} viewBox="0 0 120 100" style={{ overflow: "visible" }}>
          <path d={d} fill="none" stroke={RED} strokeWidth={6} strokeLinecap="round" pathLength={1} strokeDasharray={1} strokeDashoffset={off} />
        </svg>,
      );
    }
    case "pointer": {
      // An arrow whose tip sits at (x, y); dir = the side it comes from. Bobs towards the target.
      const rot = { left: 0, right: 180, up: 90, down: -90 }[g.dir ?? "left"] ?? 0;
      const back = (1 - pop) * 260;
      return (
        <div style={{ position: "absolute", left: x, top: y, transform: `rotate(${rot}deg) translate(${-w - back}px, ${-w * 0.25}px)`, transformOrigin: "0 0" }}>
          <svg width={w} height={w * 0.5} viewBox="0 0 200 100">
            <path d="M8 38 L120 38 L120 12 L194 50 L120 88 L120 62 L8 62 Z" fill={RED} stroke={INK} strokeWidth={9} strokeLinejoin="round" />
          </svg>
        </div>
      );
    }
    default:
      return null;
  }
};

// One graphic, appearing `enterFrame` frames into the shot, with its sound.
export const GraphicLayer: React.FC<{ g: Graphic; enterFrame: number; seed: number; volume: number }> = ({ g, enterFrame, seed, volume }) => {
  const sound = g.sfx === undefined ? SOUND[g.type] : g.sfx;
  return (
    <Sequence from={enterFrame}>
      <Body g={g} seed={seed} />
      {sound ? <Sfx name={sound} seed={seed} volume={volume} /> : null}
      {/* A stamp also gets a punch under it, so it slams rather than taps. */}
      {g.type === "stamp" && g.sfx === undefined ? <Sfx name="impact" seed={seed} volume={volume * 0.6} /> : null}
      {/* Counters tick while counting and ding when they land. */}
      {g.type === "counter" && g.sfx === undefined
        ? [4, 8, 12, 16].map((t) => <Sequence key={t} from={t}><Sfx name="tick" seed={seed} volume={volume * 0.7} /></Sequence>)
        : null}
      {g.type === "counter" && g.sfx === undefined ? <Sequence from={COUNT_FRAMES}><Sfx name="ding" seed={seed} volume={volume} /></Sequence> : null}
    </Sequence>
  );
};
