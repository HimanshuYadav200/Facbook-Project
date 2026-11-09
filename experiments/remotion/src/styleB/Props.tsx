// Flat props in the same thick-outline style: phone with chart, big arrows, money, sign, grandma.
import React from "react";

const INK = "#111";

export const Phone: React.FC<{ trend: "up" | "down" | "flat" }> = ({ trend }) => {
  const line =
    trend === "up" ? "M30 210 L80 180 L120 195 L170 110 L210 60" :
    trend === "down" ? "M30 70 L80 90 L120 80 L170 170 L210 220" :
    "M30 140 L80 125 L120 150 L170 130 L210 140";
  const c = trend === "up" ? "#2fbf4a" : trend === "down" ? "#e23b3b" : "#999";
  return (
    <svg viewBox="0 0 240 420" width="100%" height="100%">
      <rect x={6} y={6} width={228} height={408} rx={34} fill="#333" stroke={INK} strokeWidth={10} />
      <rect x={22} y={40} width={196} height={330} rx={14} fill="#f7f7f7" />
      <text x={36} y={80} fontFamily="Arial Black, Arial" fontWeight={900} fontSize={30} fill={INK}>STONK</text>
      <g transform="translate(0 60)">
        <path d={line} fill="none" stroke={c} strokeWidth={14} strokeLinecap="round" strokeLinejoin="round" />
      </g>
    </svg>
  );
};

export const BigArrow: React.FC<{ dir: "up" | "down" }> = ({ dir }) => (
  <svg viewBox="0 0 300 400" width="100%" height="100%">
    <g transform={dir === "down" ? "rotate(180 150 200)" : undefined}>
      <path d="M150 20 L280 180 L200 180 L200 380 L100 380 L100 180 L20 180 Z"
        fill={dir === "up" ? "#36c95a" : "#ec4040"} stroke={INK} strokeWidth={14} strokeLinejoin="round" />
    </g>
  </svg>
);

export const Money: React.FC<{ count?: number }> = ({ count = 4 }) => (
  <svg viewBox="0 0 300 300" width="100%" height="100%">
    {Array.from({ length: count }).map((_, i) => (
      <g key={i} transform={`translate(${(i % 2) * 18} ${200 - i * 34})`}>
        <rect x={30} y={0} width={220} height={70} rx={10} fill="#7ed37a" stroke={INK} strokeWidth={9} />
        <circle cx={140} cy={35} r={22} fill="#b9f0b5" stroke={INK} strokeWidth={6} />
        <text x={140} y={47} textAnchor="middle" fontFamily="Arial Black, Arial" fontSize={32} fill={INK}>$</text>
      </g>
    ))}
  </svg>
);

export const Sign: React.FC<{ lines: string[]; bg?: string }> = ({ lines, bg = "#fff" }) => (
  <svg viewBox="0 0 600 300" width="100%" height="100%">
    <rect x={10} y={10} width={580} height={280} rx={24} fill={bg} stroke={INK} strokeWidth={14} />
    {lines.map((l, i) => (
      <text key={i} x={300} y={150 + (i - (lines.length - 1) / 2) * 92 + 28} textAnchor="middle"
        fontFamily="Arial Black, Arial" fontWeight={900} fontSize={l.length > 12 ? 58 : 80} fill={INK}>{l}</text>
    ))}
  </svg>
);

export const Grandma: React.FC<{ asleep?: boolean }> = ({ asleep }) => (
  <svg viewBox="0 0 400 520" width="100%" height="100%">
    {/* armchair */}
    <rect x={20} y={200} width={360} height={300} rx={50} fill={INK} />
    <rect x={28} y={208} width={344} height={284} rx={44} fill="#b8483e" />
    <rect x={60} y={330} width={280} height={150} rx={30} fill="#9b3a32" stroke={INK} strokeWidth={8} />
    {/* body */}
    <path d="M110 420 q0 -150 90 -150 q90 0 90 150z" fill="#8e6cc9" stroke={INK} strokeWidth={10} />
    {/* head */}
    <circle cx={200} cy={200} r={82} fill="#f2c9a0" stroke={INK} strokeWidth={10} />
    <circle cx={200} cy={110} r={40} fill="#d9d9d9" stroke={INK} strokeWidth={9} />
    <path d="M122 180 q78 -80 156 0" fill="#d9d9d9" stroke={INK} strokeWidth={9} />
    {/* glasses + eyes */}
    <g stroke={INK} strokeWidth={7} fill="none">
      <circle cx={170} cy={205} r={24} /><circle cx={232} cy={205} r={24} /><line x1={194} y1={205} x2={208} y2={205} />
      {asleep ? (<><path d="M158 208 q12 10 24 0" /><path d="M220 208 q12 10 24 0" /></>) : null}
    </g>
    {!asleep ? (<><circle cx={170} cy={205} r={7} fill={INK} /><circle cx={232} cy={205} r={7} fill={INK} /></>) : null}
    <path d="M178 250 q22 16 44 0" stroke={INK} strokeWidth={7} fill="none" strokeLinecap="round" />
    {asleep ? (
      <g fontFamily="Arial Black, Arial" fill="#fff" stroke={INK} strokeWidth={4}>
        <text x={300} y={110} fontSize={60}>Z</text><text x={340} y={60} fontSize={44}>z</text>
      </g>
    ) : null}
  </svg>
);

// White streaks across the frame to sell fast movement.
export const SpeedLines: React.FC<{ frame: number }> = ({ frame }) => (
  <svg viewBox="0 0 1080 1920" width="100%" height="100%" style={{ position: "absolute", inset: 0 }}>
    {Array.from({ length: 14 }).map((_, i) => {
      const y = (i * 137 + (frame % 3) * 23) % 1920;
      const x = ((i * 389 + frame * 90) % 1600) - 400;
      return <line key={i} x1={x} y1={y} x2={x + 260 + (i % 3) * 80} y2={y} stroke="#fff" strokeWidth={10} strokeLinecap="round" opacity={0.85} />;
    })}
  </svg>
);
