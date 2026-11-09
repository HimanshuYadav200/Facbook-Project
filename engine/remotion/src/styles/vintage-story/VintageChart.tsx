// Vintage paper chart: "$X invested in Y", log scale, drawn progressively.
// Everything shown comes from the plan's chart settings and the run's data file (fetch_data.py format),
// using the same maths as finance_calc.py invest: value = amount * price / start price.
// The line grows from the previous shot's end date (fromDate) to this shot's `to` date.
import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig, Easing } from "remotion";
import { DataFile } from "../../common/timing";

export type ChartSpec = { data: string; amount: number; start: string; title: string; subtitle: string };
type Pt = { date: string; v: number };

const W = 1080, H = 1920;
const PAD_L = 150, PAD_R = 90, TOP = 600, BOTTOM = 1300;
const INK = "#2a2118";
const COLORS: Record<string, string> = { ink: INK, red: "#9b2d20", gold: "#9a6a12" };

const fmt = (v: number) => "$" + Math.round(v).toLocaleString("en-US");
const short = (v: number) => (v >= 1e6 ? `$${v / 1e6}M` : v >= 1e3 ? `$${v / 1e3}K` : `$${v}`);

// Index of the last point on or before `date`; fails loudly instead of drawing garbage.
const indexOn = (pts: Pt[], date: string) => {
  let i = -1;
  for (let k = 0; k < pts.length && pts[k].date <= date; k++) i = k;
  if (i < 0) throw new Error(`Chart: ${date} is before the chart start ${pts[0].date}`);
  return i;
};

export function chartPoints(spec: ChartSpec, data: DataFile): Pt[] {
  const s = data.series.filter((p) => p.date >= spec.start);
  if (s.length < 2) throw new Error(`Chart: no data after ${spec.start} in ${data.name}`);
  return s.map((p) => ({ date: p.date, v: (spec.amount * p.value) / s[0].value }));
}

export const VintageChart: React.FC<{
  spec: ChartSpec; data: DataFile; fromDate: string; toDate: string; durationFrames: number; color?: string;
}> = ({ spec, data, fromDate, toDate, durationFrames, color }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const points = chartPoints(spec, data);
  const n = points.length;
  const i0 = indexOn(points, fromDate);
  const i1 = indexOn(points, toDate);
  const x = (i: number) => PAD_L + (i / (n - 1)) * (W - PAD_L - PAD_R);
  const vals = points.map((p) => p.v);
  const lmin = Math.log10(Math.min(...vals) * 0.7), lmax = Math.log10(Math.max(...vals) * 1.4);
  const y = (v: number) => BOTTOM - ((Math.log10(v) - lmin) / (lmax - lmin)) * (BOTTOM - TOP);

  // Draw over the first 75% of the shot, then hold so the number can be read.
  const prog = interpolate(frame, [4, durationFrames * 0.75], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic),
  });
  const head = i0 + (i1 - i0) * prog;
  const hi = Math.floor(head);
  const frac = head - hi;
  const next = points[Math.min(hi + 1, n - 1)];
  const curV = points[hi].v + (next.v - points[hi].v) * frac;
  const path = (a: number, b: number) => points.slice(a, b + 1).map((p, k) => `${k ? "L" : "M"}${x(a + k).toFixed(1)} ${y(p.v).toFixed(1)}`).join(" ");
  // Earlier chart shots' part of the line stays ink; only this shot's new part is coloured.
  const oldPath = path(0, i0);
  const newPath = `${path(i0, hi)} L${x(hi + frac).toFixed(1)} ${y(curV).toFixed(1)}`;
  const lineColor = COLORS[color ?? (points[i1].v < points[i0].v ? "red" : "ink")] ?? INK;
  const pop = spring({ frame, fps, config: { damping: 14 } });
  const year = points[Math.min(Math.round(head), n - 1)].date.slice(0, 4);

  // Gridlines at powers of ten inside the range; at most ~6 year labels.
  const grid = [1, 10, 100, 1e3, 1e4, 1e5, 1e6, 1e7].filter((g) => Math.log10(g) > lmin && Math.log10(g) < lmax);
  const y0 = +points[0].date.slice(0, 4), y1 = +points[n - 1].date.slice(0, 4);
  const stepYears = Math.max(1, Math.ceil((y1 - y0 + 1) / 6));
  const years: number[] = [];
  for (let yr = y0; yr <= y1; yr += stepYears) years.push(yr);

  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" height="100%">
      <rect width={W} height={H} fill="#e8dcc0" />
      <rect x={40} y={40} width={W - 80} height={H - 80} fill="none" stroke={INK} strokeWidth={6} />
      <rect x={56} y={56} width={W - 112} height={H - 112} fill="none" stroke={INK} strokeWidth={2} />
      <text x={W / 2} y={200} textAnchor="middle" fontFamily="Georgia, 'Times New Roman', serif" fontSize={54} fill={INK} letterSpacing={4}>
        {spec.title}
      </text>
      <text x={W / 2} y={262} textAnchor="middle" fontFamily="Georgia, serif" fontSize={34} fill={INK} fontStyle="italic">
        {spec.subtitle}
      </text>
      <text x={W / 2} y={470} textAnchor="middle" fontFamily="Georgia, serif" fontWeight={700}
        fontSize={150} fill={lineColor} transform={`translate(${W / 2} 420) scale(${0.85 + 0.15 * pop}) translate(${-W / 2} -420)`}>
        {fmt(curV)}
      </text>
      {grid.map((g) => (
        <g key={g}>
          <line x1={PAD_L} x2={W - PAD_R} y1={y(g)} y2={y(g)} stroke={INK} strokeWidth={2} strokeDasharray="10 10" opacity={0.45} />
          <text x={PAD_L - 16} y={y(g) + 12} textAnchor="end" fontFamily="Georgia, serif" fontSize={32} fill={INK}>{short(g)}</text>
        </g>
      ))}
      {years.map((yr) => {
        const i = points.findIndex((p) => p.date.startsWith(String(yr)));
        return i < 0 ? null : (
          <text key={yr} x={x(i)} y={BOTTOM + 60} textAnchor="middle" fontFamily="Georgia, serif" fontSize={32} fill={INK}>{yr}</text>
        );
      })}
      <line x1={PAD_L} x2={W - PAD_R} y1={BOTTOM} y2={BOTTOM} stroke={INK} strokeWidth={4} />
      {i0 > 0 ? <path d={oldPath} fill="none" stroke={INK} strokeWidth={7} strokeLinejoin="round" strokeLinecap="round" opacity={0.75} /> : null}
      <path d={newPath} fill="none" stroke={lineColor} strokeWidth={9} strokeLinejoin="round" strokeLinecap="round" />
      <circle cx={x(hi + frac)} cy={y(curV)} r={16} fill={lineColor} stroke="#e8dcc0" strokeWidth={5} />
      <text x={W / 2} y={BOTTOM + 150} textAnchor="middle" fontFamily="Georgia, serif" fontSize={70} fill={INK}>{year}</text>
      {/* two short lines: one long line ran off the frame */}
      <text x={W / 2} y={H - 120} textAnchor="middle" fontFamily="Georgia, serif" fontSize={24} fill={INK} opacity={0.7}>
        {`${data.resolution} ${data.basis} · log scale`}
      </text>
      <text x={W / 2} y={H - 84} textAnchor="middle" fontFamily="Georgia, serif" fontSize={24} fill={INK} opacity={0.7}>
        {`source: ${data.source}`}
      </text>
    </svg>
  );
};
