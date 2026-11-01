import { useState } from 'react';

export default function PromptBlock({
  prompt,
  sha256,
  language,
  maxChars,
}: {
  prompt: string;
  sha256: string;
  language: string;
  maxChars?: number;
}) {
  const [copied, setCopied] = useState(false);
  const shown = maxChars && prompt.length > maxChars ? prompt.slice(0, maxChars) + '…' : prompt;

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(prompt);
    } catch {
      const ta = document.createElement('textarea');
      ta.value = prompt;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      ta.remove();
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 1600);
  };

  return (
    <div className="prompt-block">
      <div className="head">
        <b>Frozen prompt</b>
        <span className="muted">
          {language} · {prompt.length.toLocaleString()} chars · sha256{' '}
          <span className="mono">{sha256.slice(0, 12)}…</span>
        </span>
        <button className="copy-btn" onClick={copy}>
          {copied ? '✓ Copied' : 'Copy prompt'}
        </button>
      </div>
      <pre>{shown}</pre>
    </div>
  );
}
