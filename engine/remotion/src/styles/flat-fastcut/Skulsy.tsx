// Skulsy as a flat 2D rig: skull head + hoodie body, swappable expression and arm angles.
// Drawn in a 400x700 box. Outline trick: each shape is drawn twice, thick black stroke underneath,
// plain fill on top, so overlapping parts merge into one clean silhouette.
import React from "react";

export type Expression = "happy" | "normal" | "shocked" | "panic" | "smug" | "crying";

type Props = {
  expression: Expression;
  hoodie?: string;
  leftArm?: number; // degrees, 0 = hanging down, 90 = pointing out sideways, 160 = raised
  rightArm?: number;
  holding?: React.ReactNode; // drawn at the right hand
  jitter?: number; // small per-frame offset for panic eyes
};

const BONE = "#f3efe2";
const INK = "#111";
const OUT = 14;

const Arm: React.FC<{ x: number; y: number; angle: number; side: 1 | -1; color: string; children?: React.ReactNode }> = ({
  x, y, angle, side, color, children,
}) => {
  // Rotate around the shoulder; positive angle lifts the arm away from the body.
  const rot = side * angle;
  return (
    <g transform={`translate(${x} ${y}) rotate(${rot})`}>
      <line x1={0} y1={0} x2={0} y2={150} stroke={INK} strokeWidth={46 + OUT / 2} strokeLinecap="round" />
      <line x1={0} y1={0} x2={0} y2={150} stroke={color} strokeWidth={40} strokeLinecap="round" />
      <circle cx={0} cy={165} r={24} fill={BONE} stroke={INK} strokeWidth={7} />
      {children ? <g transform={`translate(0 175) rotate(${-rot})`}>{children}</g> : null}
    </g>
  );
};

const Eyes: React.FC<{ e: Expression; jitter: number }> = ({ e, jitter }) => {
  const L = 160, R = 240, Y = 200;
  if (e === "happy")
    return (
      <g stroke={INK} strokeWidth={10} fill="none" strokeLinecap="round">
        <path d={`M${L - 24} ${Y + 8} Q${L} ${Y - 26} ${L + 24} ${Y + 8}`} />
        <path d={`M${R - 24} ${Y + 8} Q${R} ${Y - 26} ${R + 24} ${Y + 8}`} />
      </g>
    );
  if (e === "smug")
    return (
      <g>
        <ellipse cx={L} cy={Y} rx={26} ry={24} fill={INK} />
        <ellipse cx={R} cy={Y} rx={26} ry={24} fill={INK} />
        <rect x={L - 32} y={Y - 30} width={64} height={28} fill={BONE} />
        <rect x={R - 32} y={Y - 30} width={64} height={28} fill={BONE} />
        <line x1={L - 30} y1={Y - 2} x2={L + 30} y2={Y - 2} stroke={INK} strokeWidth={8} strokeLinecap="round" />
        <line x1={R - 30} y1={Y - 2} x2={R + 30} y2={Y - 2} stroke={INK} strokeWidth={8} strokeLinecap="round" />
        <circle cx={L + 8} cy={Y + 8} r={6} fill="#fff" />
        <circle cx={R + 8} cy={Y + 8} r={6} fill="#fff" />
      </g>
    );
  const big = e === "shocked" || e === "panic";
  const rx = big ? 33 : 26, ry = big ? 40 : 30, pr = big ? 5 : 7;
  return (
    <g>
      <ellipse cx={L} cy={Y} rx={rx} ry={ry} fill={INK} />
      <ellipse cx={R} cy={Y} rx={rx} ry={ry} fill={INK} />
      <circle cx={L + jitter} cy={Y - 4} r={pr} fill="#fff" />
      <circle cx={R + jitter} cy={Y - 4} r={pr} fill="#fff" />
      {e === "crying" ? (
        <g fill="#6ec6ff" stroke={INK} strokeWidth={5}>
          <path d={`M${L - 10} ${Y + 28} q-10 60 0 120 q14 -60 12 -120z`} />
          <path d={`M${R + 10} ${Y + 28} q10 60 0 120 q-14 -60 -12 -120z`} />
        </g>
      ) : null}
    </g>
  );
};

export const Skulsy: React.FC<Props> = ({ expression, hoodie = "#3d7be0", leftArm = 10, rightArm = 10, holding, jitter = 0 }) => {
  const open = expression === "shocked" || expression === "panic" || expression === "crying";
  const jawDrop = open ? 26 : 0;
  return (
    <svg viewBox="0 0 400 700" width="100%" height="100%" style={{ overflow: "visible" }}>
      {/* legs */}
      {[150, 250].map((x) => (
        <g key={x}>
          <rect x={x - 32} y={520} width={64} height={160} rx={28} fill={INK} />
          <rect x={x - 26} y={526} width={52} height={148} rx={24} fill={hoodie} />
        </g>
      ))}
      {/* arms behind torso */}
      <Arm x={128} y={370} angle={leftArm} side={1} color={hoodie} />
      <Arm x={272} y={370} angle={rightArm} side={-1} color={hoodie}>{holding}</Arm>
      {/* torso */}
      <rect x={110} y={330} width={180} height={230} rx={50} fill={INK} />
      <rect x={117} y={337} width={166} height={216} rx={44} fill={hoodie} />
      <path d="M150 470 h100 v40 a10 10 0 0 1 -10 10 h-80 a10 10 0 0 1 -10 -10z" fill="none" stroke={INK} strokeWidth={6} opacity={0.6} />
      {/* skull: outline pass then fill pass */}
      <g>
        <ellipse cx={200} cy={200} rx={102} ry={96} fill={INK} />
        <rect x={133} y={232 + jawDrop} width={134} height={100} rx={36} fill={INK} />
        <rect x={152} y={290} width={96} height={30 + jawDrop} fill={INK} />
        <ellipse cx={200} cy={200} rx={95} ry={89} fill={BONE} />
        <rect x={140} y={239 + jawDrop} width={120} height={86} rx={30} fill={BONE} />
      </g>
      {open ? <rect x={160} y={276} width={80} height={14 + jawDrop} rx={8} fill={INK} /> : null}
      <Eyes e={expression} jitter={jitter} />
      {/* nose */}
      <path d="M200 238 l-13 22 h26z" fill={INK} />
      {/* teeth */}
      <g stroke={INK} strokeWidth={5}>
        <line x1={156} y1={290 + jawDrop} x2={244} y2={290 + jawDrop} />
        {[172, 188, 204, 220].map((x) => (
          <line key={x} x1={x + 4} y1={280 + jawDrop} x2={x + 4} y2={300 + jawDrop} />
        ))}
      </g>
      {expression === "panic" ? (
        <g fill="#8fd3ff" stroke={INK} strokeWidth={5}>
          <path d="M300 130 q16 26 0 40 q-16 -14 0 -40z" />
          <path d="M92 150 q14 22 0 34 q-14 -12 0 -34z" />
        </g>
      ) : null}
    </svg>
  );
};
