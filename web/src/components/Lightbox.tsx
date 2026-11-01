import { useEffect } from 'react';

export default function Lightbox({
  src,
  caption,
  onClose,
}: {
  src: string;
  caption: string;
  onClose: () => void;
}) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  return (
    <div className="lightbox" onClick={onClose} role="dialog" aria-modal="true" aria-label={caption}>
      <img src={src} alt={caption} />
      <div className="cap">{caption} — click anywhere or press Esc to close</div>
    </div>
  );
}
