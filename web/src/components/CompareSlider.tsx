import { useCallback, useRef, useState } from 'react';

/** Drag-to-compare slider for two same-aspect images. Pure pointer events,
 * works on touch. A/B labels support the blind-swap feature (labels are
 * passed in by the caller, so the caller can randomize sides). */
export default function CompareSlider({
  leftSrc,
  rightSrc,
  leftLabel,
  rightLabel,
  alt,
}: {
  leftSrc: string;
  rightSrc: string;
  leftLabel: string;
  rightLabel: string;
  alt: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [pos, setPos] = useState(50);

  const move = useCallback((clientX: number) => {
    const el = ref.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const pct = ((clientX - rect.left) / rect.width) * 100;
    setPos(Math.min(98, Math.max(2, pct)));
  }, []);

  return (
    <div
      className="slider-compare"
      ref={ref}
      style={{ ['--pos' as string]: `${pos}%` }}
      onPointerDown={(e) => {
        (e.target as HTMLElement).setPointerCapture?.(e.pointerId);
        move(e.clientX);
      }}
      onPointerMove={(e) => e.buttons > 0 && move(e.clientX)}
    >
      <img src={leftSrc} alt={`${alt} — ${leftLabel}`} draggable={false} />
      <div className="after">
        <img src={rightSrc} alt={`${alt} — ${rightLabel}`} draggable={false} />
      </div>
      <span className="label l">{leftLabel}</span>
      <span className="label r">{rightLabel}</span>
      <div className="handle" />
    </div>
  );
}
