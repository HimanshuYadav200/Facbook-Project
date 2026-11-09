// Style "vintage-story": narrated story in an old-film look. Reads the run's plan.json, words.json, data files.
// Image shots get camera motion + colour grade; chart shots draw real data; film effects on top.
// Shot fields are documented in .claude/skills/style-vintage-story/SKILL.md.
import React from "react";
import {
  AbsoluteFill, Audio, Img, Sequence, interpolate, random, spring, staticFile, useCurrentFrame, useVideoConfig, Easing,
} from "remotion";
import { AudioBed } from "../../common/AudioBed";
import { Caption } from "../../common/Caption";
import { BasePlan, DataFile, Word, sfxFile, shotStarts, secToFrame } from "../../common/timing";
import { ChartSpec, VintageChart } from "./VintageChart";

type Shot = {
  from: number; type: "image" | "chart"; sfx?: string;
  // image shots
  img?: string; motion?: string; zoom?: number; focus?: [number, number]; grade?: "mono" | "warm";
  stamp?: string; flash?: boolean; shake?: boolean; sticker?: { text: string; x: number; y: number };
  // chart shots
  chart?: string; to?: string; color?: "ink" | "red" | "gold";
  // extra SFX tied to word indexes
  cues?: { word: number; sfx: string }[];
};
export type VintagePlan = BasePlan<Shot> & { charts?: Record<string, ChartSpec> };
export type VintageProps = { words: Word[]; duration: number; plan: VintagePlan; data: Record<string, DataFile> };

const GRADE = {
  mono: "grayscale(0.55) sepia(0.45) contrast(1.12) brightness(0.95)",
  warm: "sepia(0.12) saturate(1.08) contrast(1.06)",
};

const ImageShot: React.FC<{ s: Shot; len: number; idx: number }> = ({ s, len, idx }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = interpolate(frame, [0, len], [0, 1], { extrapolateRight: "clamp", easing: Easing.out(Easing.quad) });
  const z = s.zoom ?? 1.1;
  const [fx, fy] = s.focus ?? [0.5, 0.5];
  let scale = z, dx = 0, dy = 0;
  switch (s.motion) {
    case "pushIn": scale = z * (1 + 0.12 * t); break;
    case "pullOut": scale = z * (1.14 - 0.12 * t); break;
    case "panL": dx = 60 - 120 * t; break;
    case "panR": dx = -60 + 120 * t; break;
    case "panUp": dy = 80 - 160 * t; break;
    case "panDown": dy = -80 + 160 * t; break;
  }
  const shakeAmt = s.shake ? 18 * Math.max(0, 1 - frame / 18) : 0;
  const shakeX = shakeAmt ? (random(`sx${idx}-${Math.floor(frame / 2)}`) - 0.5) * shakeAmt : 0;
  const shakeY = shakeAmt ? (random(`sy${idx}-${Math.floor(frame / 2)}`) - 0.5) * shakeAmt : 0;
  const stampPop = spring({ frame: frame - 2, fps, config: { damping: 10, stiffness: 220 } });
  const flash = s.flash ? interpolate(frame, [0, 8], [0.9, 0], { extrapolateRight: "clamp" }) : 0;
  return (
    <AbsoluteFill style={{ overflow: "hidden", background: "#111" }}>
      <Img src={staticFile(`img/${s.img}`)} style={{
        width: "100%", height: "100%", objectFit: "cover",
        transformOrigin: `${fx * 100}% ${fy * 100}%`,
        transform: `translate(${dx + shakeX}px, ${dy + shakeY}px) scale(${scale})`,
        filter: GRADE[s.grade ?? "mono"],
      }} />
      {s.sticker ? (
        <div style={{
          position: "absolute", left: `${s.sticker.x * 100}%`, top: `${s.sticker.y * 100}%`,
          transform: `translate(-50%,-50%) rotate(-6deg) scale(${stampPop})`,
          background: "#f3e6c4", color: "#2a2118", border: "6px solid #2a2118", padding: "10px 26px",
          fontFamily: "Georgia, serif", fontWeight: 700, fontSize: 64,
        }}>{s.sticker.text}</div>
      ) : null}
      {s.stamp ? (
        <div style={{ position: "absolute", top: "16%", width: "100%", textAlign: "center" }}>
          <span style={{
            display: "inline-block", transform: `scale(${1.6 - 0.6 * stampPop}) rotate(-3deg)`, opacity: stampPop,
            fontFamily: "Georgia, 'Times New Roman', serif", fontSize: 120, letterSpacing: 10, color: "#f4ead2",
            padding: "8px 40px", border: "6px double #f4ead2", background: "rgba(20,14,8,0.55)",
            textShadow: "0 4px 12px rgba(0,0,0,0.7)",
          }}>{s.stamp}</span>
        </div>
      ) : null}
      {flash ? <AbsoluteFill style={{ background: "#fff8e0", opacity: flash }} /> : null}
    </AbsoluteFill>
  );
};

// Film look on top of everything: grain, flicker, vignette, occasional scratch and dust.
const FilmLook: React.FC = () => {
  const frame = useCurrentFrame();
  const flicker = 0.035 * (random(`f${frame}`) - 0.5);
  const scratch = random(`s${Math.floor(frame / 3)}`) > 0.82;
  const sx = random(`sx${Math.floor(frame / 3)}`) * 1080;
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <svg width="100%" height="100%" viewBox="0 0 1080 1920" style={{ position: "absolute", inset: 0, mixBlendMode: "overlay", opacity: 0.5 }}>
        <filter id="grain"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves={2} seed={frame % 50} /><feColorMatrix type="saturate" values="0" /></filter>
        <rect width="1080" height="1920" filter="url(#grain)" />
      </svg>
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at center, rgba(0,0,0,0) 45%, rgba(0,0,0,0.65) 100%)" }} />
      <AbsoluteFill style={{ background: flicker > 0 ? "#fff" : "#000", opacity: Math.abs(flicker) }} />
      {scratch ? <div style={{ position: "absolute", left: sx, top: 0, width: 2, height: "100%", background: "rgba(255,250,235,0.35)" }} /> : null}
      {Array.from({ length: 3 }).map((_, i) => random(`d${frame}-${i}`) > 0.6 ? (
        <div key={i} style={{
          position: "absolute", left: random(`dx${frame}-${i}`) * 1080, top: random(`dy${frame}-${i}`) * 1920,
          width: 4 + random(`dw${frame}-${i}`) * 6, height: 4 + random(`dh${frame}-${i}`) * 6, borderRadius: "50%",
          background: "rgba(20,15,10,0.6)",
        }} />
      ) : null)}
    </AbsoluteFill>
  );
};

export const VintageStory: React.FC<VintageProps> = ({ words, duration, plan, data }) => {
  const frame = useCurrentFrame();
  const shots = plan.shots;
  const starts = shotStarts(shots.map((s) => s.from), words).map(secToFrame);
  const endFrom = secToFrame(duration + (plan.tailSeconds ?? 0.4));
  // Gate weave: whole frame drifts a pixel or two, like an old projector.
  const weaveX = (random(`wx${Math.floor(frame / 2)}`) - 0.5) * 3;
  const weaveY = (random(`wy${Math.floor(frame / 2)}`) - 0.5) * 3;
  const chartEnd: Record<string, string> = {}; // where each chart's line got to in earlier shots
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      <AbsoluteFill style={{ transform: `translate(${weaveX}px, ${weaveY}px) scale(1.01)` }}>
        {shots.map((s, i) => {
          const from = starts[i];
          const to = i + 1 < starts.length ? starts[i + 1] : endFrom;
          const len = Math.max(1, to - from);
          let body: React.ReactNode;
          if (s.type === "chart") {
            const spec = plan.charts?.[s.chart ?? ""];
            if (!spec) throw new Error(`Shot ${i}: unknown chart "${s.chart}"`);
            const d = data[spec.data];
            if (!d) throw new Error(`Shot ${i}: chart data "${spec.data}" not listed in plan.data`);
            body = <VintageChart spec={spec} data={d} fromDate={chartEnd[s.chart!] ?? spec.start} toDate={s.to!} durationFrames={len} color={s.color} />;
            chartEnd[s.chart!] = s.to!;
          } else {
            body = <ImageShot s={s} len={len} idx={i} />;
          }
          return (
            <Sequence key={i} from={from} durationInFrames={len}>
              {body}
              {s.sfx ? <Audio src={sfxFile(s.sfx)} volume={0.3} /> : null}
            </Sequence>
          );
        })}
        {shots.flatMap((s) => s.cues ?? []).map((c, i) => (
          <Sequence key={`c${i}`} from={secToFrame(words[c.word].start)}>
            <Audio src={sfxFile(c.sfx)} volume={0.35} />
          </Sequence>
        ))}
        {plan.endCard ? (
          <Sequence from={endFrom}>
            <AbsoluteFill style={{ background: "#0b0805", justifyContent: "center", alignItems: "center" }}>
              <span style={{
                fontFamily: "Georgia, serif", fontSize: 110, letterSpacing: 24, color: "#e9b860",
                textShadow: "0 0 30px rgba(233,184,96,0.6)", opacity: interpolate(frame - endFrom, [0, 15], [0, 1], { extrapolateRight: "clamp" }),
              }}>{plan.endCard.text}</span>
            </AbsoluteFill>
            <Audio src={sfxFile("thud")} volume={0.3} />
          </Sequence>
        ) : null}
      </AbsoluteFill>
      <FilmLook />
      <AudioBed plan={plan} />
      {frame < endFrom ? (
        <Caption words={words} top="80%" uppercase style={{
          fontFamily: "Georgia, 'Times New Roman', serif", fontSize: 64, letterSpacing: 3, color: "#fbf5e6",
          textShadow: "0 3px 10px rgba(0,0,0,0.85), 0 0 3px rgba(0,0,0,0.9)",
        }} />
      ) : null}
    </AbsoluteFill>
  );
};
