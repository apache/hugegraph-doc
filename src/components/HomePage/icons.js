import React from 'react';

const base = {
  width: 24,
  height: 24,
  viewBox: '0 0 24 24',
  fill: 'none',
  xmlns: 'http://www.w3.org/2000/svg',
  'aria-hidden': true,
  focusable: false,
};

const stroke = {
  stroke: 'currentColor',
  strokeWidth: 1.7,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
};

export function IconDatabase(props) {
  return (
    <svg {...base} {...props}>
      <ellipse cx="12" cy="5.5" rx="7" ry="2.8" {...stroke} />
      <path d="M5 5.5v6c0 1.55 3.13 2.8 7 2.8s7-1.25 7-2.8v-6" {...stroke} />
      <path d="M5 11.5v6c0 1.55 3.13 2.8 7 2.8s7-1.25 7-2.8v-6" {...stroke} />
    </svg>
  );
}

export function IconCompute(props) {
  return (
    <svg {...base} {...props}>
      <circle cx="6" cy="6" r="2.2" {...stroke} />
      <circle cx="18" cy="6" r="2.2" {...stroke} />
      <circle cx="12" cy="18" r="2.2" {...stroke} />
      <path d="M7.6 7.6 11 15.8M16.4 7.6 13 15.8M8.2 6h7.6" {...stroke} />
    </svg>
  );
}

export function IconAI(props) {
  return (
    <svg {...base} {...props}>
      <path d="M12 3v3M12 18v3M3 12h3M18 12h3" {...stroke} />
      <rect x="7.5" y="7.5" width="9" height="9" rx="2.4" {...stroke} />
      <circle cx="12" cy="12" r="1.8" {...stroke} />
    </svg>
  );
}

export function IconApi(props) {
  return (
    <svg {...base} {...props}>
      <path d="M8 7 4 12l4 5M16 7l4 5-4 5" {...stroke} />
      <path d="M13.5 5.5 10.5 18.5" {...stroke} />
    </svg>
  );
}

export function IconQuery(props) {
  return (
    <svg {...base} {...props}>
      <circle cx="10.5" cy="10.5" r="6.2" {...stroke} />
      <path d="m15.3 15.3 4 4" {...stroke} />
      <path d="M8 10.5h5M10.5 8v5" {...stroke} />
    </svg>
  );
}

export function IconDistributed(props) {
  return (
    <svg {...base} {...props}>
      <rect x="3.5" y="3.5" width="7" height="7" rx="1.6" {...stroke} />
      <rect x="13.5" y="3.5" width="7" height="7" rx="1.6" {...stroke} />
      <rect x="8.5" y="13.5" width="7" height="7" rx="1.6" {...stroke} />
    </svg>
  );
}

export function IconVisualize(props) {
  return (
    <svg {...base} {...props}>
      <circle cx="6" cy="8" r="2.1" {...stroke} />
      <circle cx="17" cy="6" r="2.1" {...stroke} />
      <circle cx="15" cy="17" r="2.1" {...stroke} />
      <circle cx="7" cy="16" r="1.6" {...stroke} />
      <path d="m7.8 8.8 7.3-1.4M7.4 14.6l6.2 1.2M7.7 9.6l6.4 6" {...stroke} />
    </svg>
  );
}

export function IconScale(props) {
  return (
    <svg {...base} {...props}>
      <path d="M12 3v18" {...stroke} />
      <path d="M5 8h14M7 8l-3 5h6zM17 8l-3 5h6z" {...stroke} />
      <path d="M8 20h8" {...stroke} />
    </svg>
  );
}

export function IconArrowRight(props) {
  return (
    <svg {...base} {...props}>
      <path d="M5 12h13M13 6l6 6-6 6" {...stroke} />
    </svg>
  );
}

export function IconGithub(props) {
  return (
    <svg {...base} {...props} fill="currentColor">
      <path d="M12 2C6.48 2 2 6.58 2 12.25c0 4.53 2.87 8.37 6.84 9.73.5.1.68-.22.68-.49l-.01-1.9c-2.78.62-3.37-1.2-3.37-1.2-.46-1.18-1.11-1.5-1.11-1.5-.91-.64.07-.62.07-.62 1 .07 1.53 1.06 1.53 1.06.9 1.56 2.36 1.11 2.93.85.09-.66.35-1.11.63-1.37-2.22-.26-4.55-1.14-4.55-5.06 0-1.12.39-2.03 1.03-2.75-.1-.26-.45-1.3.1-2.71 0 0 .84-.28 2.75 1.05a9.3 9.3 0 0 1 5 0c1.91-1.33 2.75-1.05 2.75-1.05.55 1.41.2 2.45.1 2.71.64.72 1.03 1.63 1.03 2.75 0 3.93-2.34 4.79-4.57 5.05.36.32.68.94.68 1.9l-.01 2.82c0 .27.18.59.69.49A10.04 10.04 0 0 0 22 12.25C22 6.58 17.52 2 12 2Z" />
    </svg>
  );
}

export function IconSpark(props) {
  return (
    <svg {...base} {...props}>
      <path d="M12 3.5 13.6 9 19 10.5 13.6 12 12 17.5 10.4 12 5 10.5 10.4 9z" {...stroke} />
    </svg>
  );
}

export function IconBook(props) {
  return (
    <svg {...base} {...props}>
      <path d="M4 5.5C4 4.7 4.7 4 5.5 4H11v15.5H5.5c-.8 0-1.5-.7-1.5-1.5z" {...stroke} />
      <path d="M20 5.5c0-.8-.7-1.5-1.5-1.5H13v15.5h5.5c.8 0 1.5-.7 1.5-1.5z" {...stroke} />
    </svg>
  );
}

export function IconUsers(props) {
  return (
    <svg {...base} {...props}>
      <circle cx="9" cy="8" r="3" {...stroke} />
      <path d="M3.5 19a5.5 5.5 0 0 1 11 0" {...stroke} />
      <path d="M16 5.2a3 3 0 0 1 0 5.6M17 13.5a5.5 5.5 0 0 1 3.5 5.1" {...stroke} />
    </svg>
  );
}

export function IconCommit(props) {
  return (
    <svg {...base} {...props}>
      <circle cx="12" cy="12" r="3.2" {...stroke} />
      <path d="M3 12h5.8M15.2 12H21" {...stroke} />
    </svg>
  );
}

export function IconBuilding(props) {
  return (
    <svg {...base} {...props}>
      <rect x="5" y="3.5" width="14" height="17" rx="1.6" {...stroke} />
      <path d="M9 7.5h2M13 7.5h2M9 11h2M13 11h2M9 14.5h2M13 14.5h2M10 20.5v-3h4v3" {...stroke} />
    </svg>
  );
}

export function IconGlobe(props) {
  return (
    <svg {...base} {...props}>
      <circle cx="12" cy="12" r="8.5" {...stroke} />
      <path d="M3.5 12h17M12 3.5c2.5 2.4 2.5 14.6 0 17M12 3.5c-2.5 2.4-2.5 14.6 0 17" {...stroke} />
    </svg>
  );
}

export function IconExternal(props) {
  return (
    <svg {...base} {...props}>
      <path d="M14 5h5v5M19 5l-8 8M17 13.5V18a1.5 1.5 0 0 1-1.5 1.5h-9A1.5 1.5 0 0 1 5 18V9a1.5 1.5 0 0 1 1.5-1.5H11" {...stroke} />
    </svg>
  );
}
