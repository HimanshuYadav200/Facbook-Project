// One-word-at-a-time caption, synced to the narration's word timings.
import React from "react";
import { useCurrentFrame, spring, useVideoConfig } from "remotion";
import { Word } from "./timing";

type Props = {
  words: Word[];
  style: React.CSSProperties; // font, colour, shadow
  top: string; // vertical position, e.g. "50%"
  uppercase?: boolean;
  pop?: boolean; // small scale pop when each word appears
};

export const Caption: React.FC<Props> = ({ words, style, top, uppercase, pop }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  // Show the word being spoken; hold the last word through short pauses.
  let idx = -1;
  for (let i = 0; i < words.length; i++) {
    if (words[i].start <= t) idx = i;
    else break;
  }
  if (idx < 0) return null;
  const w = words[idx];
  if (t > w.end + 0.35) return null;
  const local = frame - Math.round(w.start * fps);
  const s = pop ? spring({ frame: local, fps, config: { damping: 12, stiffness: 300 }, from: 0.7, to: 1 }) : 1;
  const text = w.word.replace(/^[^\w$']+|[^\w%']+$/g, "");
  return (
    <div style={{ position: "absolute", left: 0, right: 0, top, transform: "translateY(-50%)", textAlign: "center" }}>
      <span style={{ display: "inline-block", transform: `scale(${s})`, ...style }}>
        {uppercase ? text.toUpperCase() : text}
      </span>
    </div>
  );
};
