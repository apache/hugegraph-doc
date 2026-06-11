import React from 'react';

function CopyIcon(props) {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" aria-hidden="true" {...props}>
      <rect x="9" y="9" width="11" height="11" rx="2" stroke="currentColor" strokeWidth="1.7" />
      <path
        d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
      />
    </svg>
  );
}

function CheckIcon(props) {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" aria-hidden="true" {...props}>
      <path d="m5 12.5 4.5 4.5L19 7" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function TerminalBlock({title, lines, plain, copyLabel = 'Copy', copiedLabel = 'Copied'}) {
  const [copied, setCopied] = React.useState(false);
  const timerRef = React.useRef(null);

  React.useEffect(() => () => timerRef.current && clearTimeout(timerRef.current), []);

  function onCopy() {
    const text = plain || lines.map((line) => line.text).join('\n');
    const done = () => {
      setCopied(true);
      timerRef.current && clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => setCopied(false), 2000);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done).catch(() => {});
    } else {
      done();
    }
  }

  return (
    <div className="hgTerminal">
      <div className="hgTerminal__bar">
        <span className="hgTerminal__dots" aria-hidden="true">
          <span className="hgTerminal__dot" />
          <span className="hgTerminal__dot" />
          <span className="hgTerminal__dot" />
        </span>
        <span className="hgTerminal__title">{title}</span>
        <button
          type="button"
          className="hgTerminal__copy"
          onClick={onCopy}
          aria-label={copied ? copiedLabel : copyLabel}>
          {copied ? <CheckIcon /> : <CopyIcon />}
          <span>{copied ? copiedLabel : copyLabel}</span>
        </button>
      </div>
      <pre className="hgTerminal__body">
        <code>
          {lines.map((line, i) => {
            if (line.type === 'blank') {
              return <span className="hgTerminal__line" key={i}>{'\u00a0'}</span>;
            }
            return (
              <span className={`hgTerminal__line hgTerminal__line--${line.type}`} key={i}>
                {line.type === 'cmd' && <span className="hgTerminal__prompt">$ </span>}
                {line.text}
              </span>
            );
          })}
        </code>
      </pre>
    </div>
  );
}

export default TerminalBlock;
