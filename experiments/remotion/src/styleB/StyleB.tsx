// Style B renderer: reads plan.json (shots + layers) and words.json, draws flat 2D shots
// with constant hand-drawn wobble, camera shake, pop/drop entrances, SFX on every cut.
import React from "react";
import {
  AbsoluteFill, Audio, Sequence, random, spring, staticFile, useCurrentFrame, useVideoConfig,
} from "remotion";
import { Caption } from "../common/Caption";
import { Word, shotStarts, secToFrame } from "../common/timing";
import { Skulsy } from "./Skulsy";
import { BigArrow, Grandma, Money, Phone, Sign, SpeedLines } from "./Props";

type Layer = { type: string; x: number; y: number; w: number; h: number; enter?: string; props?: any };
type Shot = { from: number; bg: string; sfx?: string; shake?: number; speedLines?: boolean; push?: boolean; layers: Layer[] };
export type StyleBProps = { words: Word[]; duration: number; plan: { shots: Shot[] } };

const renderLayer = (l: Layer, frame: number) => {
  const p = l.props || {};
  switch (l.type) {
    case "skulsy": {
      const holding =
        p.holding === "money" ? <g transform="translate(-110 -90) scale(0.8)"><foreignObject width={300} height={300}><Money count={2} /></foreignObject></g> :
        p.holding?.startsWith("phone") ? <g transform="translate(-75 -190) scale(0.65)"><foreignObject width={240} height={420}><Phone trend={p.holding.split("-")[1]} /></foreignObject></g> :
        undefined;
      const jitter = p.expression === "panic" ? (random(`j${Math.floor(frame / 2)}`) - 0.5) * 10 : 0;
      return <Skulsy {...p} holding={holding} jitter={jitter} />;
    }
    case "phone": return <Phone trend={p.trend} />;
    case "arrow": return <BigArrow dir={p.dir} />;
    case "money": return <Money count={p.count} />;
    case "sign": return <Sign lines={p.lines} bg={p.bg} />;
    case "grandma": return <Grandma asleep={p.asleep} />;
    default: return null;
  }
};

// Entrance motion for a layer, measured in frames since the shot started.
const enterTransform = (kind: string | undefined, f: number, fps: number) => {
  const s = spring({ frame: f, fps, config: { damping: 9, stiffness: 260, mass: 0.6 } });
  switch (kind) {
    case "pop": return `scale(${0.55 + 0.45 * s})`;
    case "drop": return `translateY(${(1 - s) * -700}px)`;
    case "rise": return `translateY(${(1 - s) * 900}px)`;
    case "slideL": return `translateX(${(1 - s) * -900}px)`;
    case "slideR": return `translateX(${(1 - s) * 900}px)`;
    default: return "";
  }
};

const ShotView: React.FC<{ shot: Shot; idx: number }> = ({ shot, idx }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const step = Math.floor(frame / 2); // animate "on twos" like hand-drawn work
  const shake = shot.shake ?? 0;
  const camX = shake ? (random(`cx${idx}-${step}`) - 0.5) * 14 * shake : 0;
  const camY = shake ? (random(`cy${idx}-${step}`) - 0.5) * 14 * shake : 0;
  // Slow push-in keeps long shots alive.
  const zoom = (shake ? 1.04 : 1) * (shot.push ? 1 + frame * 0.004 : 1);
  return (
    <AbsoluteFill style={{ background: shot.bg, transform: `translate(${camX}px, ${camY}px) scale(${zoom})` }}>
      {shot.speedLines ? <SpeedLines frame={frame} /> : null}
      {shot.layers.map((l, i) => {
        // Constant idle wobble: tiny offset + rotation that changes every 2 frames.
        const wx = (random(`wx${idx}-${i}-${step}`) - 0.5) * 6;
        const wy = (random(`wy${idx}-${i}-${step}`) - 0.5) * 6;
        const wr = (random(`wr${idx}-${i}-${step}`) - 0.5) * 1.6;
        return (
          <div key={i} style={{
            position: "absolute", left: l.x - l.w / 2, top: l.y - l.h / 2, width: l.w, height: l.h,
            transform: `${enterTransform(l.enter, frame, fps)} translate(${wx}px, ${wy}px) rotate(${wr}deg)`,
            filter: "url(#boil)",
          }}>
            {renderLayer(l, frame)}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

export const StyleB: React.FC<StyleBProps> = ({ words, duration, plan }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const starts = shotStarts(plan.shots.map((s) => s.from), words).map(secToFrame);
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      {/* "Line boil": outlines wobble slightly, new noise pattern every 3 frames */}
      <svg width={0} height={0} style={{ position: "absolute" }}>
        <filter id="boil">
          <feTurbulence type="fractalNoise" baseFrequency="0.02" numOctaves={2} seed={Math.floor(frame / 3)} />
          <feDisplacementMap in="SourceGraphic" scale={5} />
        </filter>
      </svg>
      {plan.shots.map((shot, i) => {
        const from = starts[i];
        const to = i + 1 < starts.length ? starts[i + 1] : durationInFrames;
        return (
          <Sequence key={i} from={from} durationInFrames={Math.max(1, to - from)}>
            <ShotView shot={shot} idx={i} />
            {shot.sfx ? <Audio src={staticFile(`sfx/${shot.sfx}.wav`)} volume={0.45} /> : null}
          </Sequence>
        );
      })}
      <Audio src={staticFile("styleB/voice.wav")} />
      <Caption words={words} top="44%" pop style={{
        fontFamily: "Helvetica Neue, Arial, sans-serif", fontWeight: 900, fontSize: 118, color: "#fff",
        WebkitTextStroke: "5px #111", paintOrder: "stroke fill",
        textShadow: "0 8px 18px rgba(0,0,0,0.5)",
      }} />
    </AbsoluteFill>
  );
};
