// Vintage paper chart: "$1,000 invested in NVIDIA, Jan 2016", log scale, drawn progressively.
// The line grows from the previous chart shot's end month to this shot's `to` month.
import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig, Easing } from "remotion";

export type Point = { m: string; v: number };

const W = 1080, H = 1920;
const PAD_L = 150, PAD_R = 90, TOP = 600, BOTTOM = 1300;
const INK = "#2a2118";

const fmt = (v: number) => "$" + Math.round(v).toLocaleString("en-US");

export const VintageChart: React.FC<{ points: Point[]; fromM: string; toM: string; durationFrames: number }> = ({
  points, fromM, toM, durationFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const i0 = Math.max(0, points.findIndex((p) => p.m === fromM));
  const i1 = points.findIndex((p) => p.m === toM);
  const n = points.length;
  const x = (i: number) => PAD_L + (i / (n - 1)) * (W - PAD_L - PAD_R);
  const lmin = Math.log10(500), lmax = Math.log10(500000);
  const y = (v: number) => BOTTOM - ((Math.log10(v) - lmin) / (lmax - lmin)) * (BOTTOM - TOP);

  // Draw over the first 75% of the shot, then hold.
  const prog = interpolate(frame, [4, durationFrames * 0.75], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic),
  });
  const head = i0 + (i1 - i0) * prog;
  const hi = Math.floor(head);
  const visible = points.slice(0, hi + 1);
  const frac = head - hi;
  const next = points[Math.min(hi + 1, n - 1)];
  const curV = visible[visible.length - 1].v + (next.v - visible[visible.length - 1].v) * frac;
  // Old part of the line (drawn in earlier chart shots) stays ink; only this shot's new part gets colour.
  const oldPath = points.slice(0, i0 + 1).map((p, i) => `${i ? "L" : "M"}${x(i).toFixed(1)} ${y(p.v).toFixed(1)}`).join(" ");
  const newPath = `M${x(i0).toFixed(1)} ${y(points[i0].v).toFixed(1)} ` +
    visible.slice(i0 + 1).map((p, k) => `L${x(i0 + 1 + k).toFixed(1)} ${y(p.v).toFixed(1)}`).join(" ") +
    ` L${x(hi + frac).toFixed(1)} ${y(curV).toFixed(1)}`;
  const falling = points[i1].v < points[i0].v;
  const lineColor = falling ? "#9b2d20" : toM >= "2026" ? "#9a6a12" : INK;
  const pop = spring({ frame, fps, config: { damping: 14 } });
  const year = points[Math.min(Math.round(head), n - 1)].m.slice(0, 4);

  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" height="100%">
      <rect width={W} height={H} fill="#e8dcc0" />
      <rect x={40} y={40} width={W - 80} height={H - 80} fill="none" stroke={INK} strokeWidth={6} />
      <rect x={56} y={56} width={W - 112} height={H - 112} fill="none" stroke={INK} strokeWidth={2} />
      <text x={W / 2} y={200} textAnchor="middle" fontFamily="Georgia, 'Times New Roman', serif" fontSize={54} fill={INK} letterSpacing={4}>
        $1,000 IN NVIDIA
      </text>
      <text x={W / 2} y={262} textAnchor="middle" fontFamily="Georgia, serif" fontSize={34} fill={INK} fontStyle="italic">
        invested January 2016
      </text>
      <text x={W / 2} y={470} textAnchor="middle" fontFamily="Georgia, serif" fontWeight={700}
        fontSize={150} fill={lineColor} transform={`translate(${W / 2} 420) scale(${0.85 + 0.15 * pop}) translate(${-W / 2} -420)`}>
        {fmt(curV)}
      </text>
      {/* gridlines: log scale */}
      {[1000, 10000, 100000].map((g) => (
        <g key={g}>
          <line x1={PAD_L} x2={W - PAD_R} y1={y(g)} y2={y(g)} stroke={INK} strokeWidth={2} strokeDasharray="10 10" opacity={0.45} />
          <text x={PAD_L - 16} y={y(g) + 12} textAnchor="end" fontFamily="Georgia, serif" fontSize={32} fill={INK}>{fmt(g).replace(",000", "K")}</text>
        </g>
      ))}
      {["2016", "2018", "2020", "2022", "2024", "2026"].map((yr) => {
        const i = points.findIndex((p) => p.m.startsWith(yr));
        return i < 0 ? null : (
          <text key={yr} x={x(i)} y={BOTTOM + 60} textAnchor="middle" fontFamily="Georgia, serif" fontSize={32} fill={INK}>{yr}</text>
        );
      })}
      <line x1={PAD_L} x2={W - PAD_R} y1={BOTTOM} y2={BOTTOM} stroke={INK} strokeWidth={4} />
      {i0 > 0 ? <path d={oldPath} fill="none" stroke={INK} strokeWidth={7} strokeLinejoin="round" strokeLinecap="round" opacity={0.75} /> : null}
      <path d={newPath} fill="none" stroke={lineColor} strokeWidth={9} strokeLinejoin="round" strokeLinecap="round" />
      <circle cx={x(hi + frac)} cy={y(curV)} r={16} fill={lineColor} stroke="#e8dcc0" strokeWidth={5} />
      <text x={W / 2} y={BOTTOM + 150} textAnchor="middle" fontFamily="Georgia, serif" fontSize={70} fill={INK}>{year}</text>
      <text x={W / 2} y={H - 90} textAnchor="middle" fontFamily="Georgia, serif" fontSize={24} fill={INK} opacity={0.7}>
        Split &amp; dividend adjusted monthly close · log scale · source: Alpha Vantage
      </text>
    </svg>
  );
};
