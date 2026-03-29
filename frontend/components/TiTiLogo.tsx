'use client';

interface TiTiLogoProps {
  className?: string;
  size?: number;
}

/**
 * TiTi Logo — SVG vector.
 * First "T" is dark navy (#1B3A5C), rest (i, T, i) are teal (#1FA5A0).
 * First "i" dot: small upward triangle arrow.
 * Second "i" dot: taller growth arrow pointing up-right.
 */
export default function TiTiLogo({ className = '', size = 32 }: TiTiLogoProps) {
  const h = size;
  const w = h * 2.5;

  const navy = '#1B3A5C';
  const teal = '#1FA5A0';

  return (
    <svg
      viewBox="0 0 250 100"
      width={w}
      height={h}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-label="TiTi Logo"
    >
      {/* T1 — navy */}
      <rect x="2" y="30" width="52" height="12" rx="2" fill={navy} />
      <rect x="19" y="30" width="14" height="50" rx="2" fill={navy} />

      {/* i1 — teal, small arrow dot */}
      <rect x="62" y="46" width="12" height="34" rx="2" fill={teal} />
      <polygon points="68,20 58,35 78,35" fill={teal} />

      {/* T2 — teal */}
      <rect x="108" y="30" width="52" height="12" rx="2" fill={teal} />
      <rect x="125" y="30" width="14" height="50" rx="2" fill={teal} />

      {/* i2 — teal, growth arrow */}
      <rect x="168" y="46" width="12" height="34" rx="2" fill={teal} />
      {/* Arrow shaft going up */}
      <rect x="170" y="16" width="8" height="24" rx="1" fill={teal} />
      {/* Arrowhead pointing up-right */}
      <polygon points="174,2 164,16 176,16" fill={teal} />
      {/* Right wing of arrow (growth direction) */}
      <polygon points="176,10 176,16 196,16 196,10 186,4" fill={teal} />
    </svg>
  );
}
