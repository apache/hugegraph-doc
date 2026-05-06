import React from 'react';
import {useLocation} from '@docusaurus/router';
import Link from '@docusaurus/Link';
import versionsMetadata from '@site/src/data/versions.json';

const versions = versionsMetadata.map((version) => ({
  label: version.label,
  enTo: version.path,
  cnTo: version.cnPath,
}));

function isChinesePath(pathname) {
  return pathname === '/cn' || pathname.startsWith('/cn/');
}

function isDocsPath(pathname) {
  return pathname === '/docs' || pathname.startsWith('/docs/') || pathname === '/cn/docs' || pathname.startsWith('/cn/docs/');
}

function focusMenuItem(menuRef, offset) {
  const links = Array.from(menuRef.current?.querySelectorAll('a') || []);
  if (links.length === 0) {
    return;
  }
  const currentIndex = links.indexOf(document.activeElement);
  const nextIndex = currentIndex === -1 ? 0 : (currentIndex + offset + links.length) % links.length;
  links[nextIndex].focus();
}

export default function DocumentationDropdownNavbarItem() {
  const {pathname} = useLocation();
  const isChinese = isChinesePath(pathname);
  const [open, setOpen] = React.useState(false);
  const rootRef = React.useRef(null);
  const menuRef = React.useRef(null);

  React.useEffect(() => {
    function closeOnOutsideClick(event) {
      if (!rootRef.current?.contains(event.target)) {
        setOpen(false);
      }
    }

    document.addEventListener('mousedown', closeOnOutsideClick);
    return () => document.removeEventListener('mousedown', closeOnOutsideClick);
  }, []);

  function onButtonKeyDown(event) {
    if (event.key === 'ArrowDown' || event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      setOpen(true);
      window.requestAnimationFrame(() => focusMenuItem(menuRef, 1));
    }
    if (event.key === 'Escape') {
      setOpen(false);
    }
  }

  function onMenuKeyDown(event) {
    if (event.key === 'Escape') {
      setOpen(false);
      rootRef.current?.querySelector('button')?.focus();
    }
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      focusMenuItem(menuRef, 1);
    }
    if (event.key === 'ArrowUp') {
      event.preventDefault();
      focusMenuItem(menuRef, -1);
    }
  }

  return (
    <div
      className="navbar__item documentationDropdown"
      ref={rootRef}
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
      onFocus={() => setOpen(true)}>
      <button
        aria-expanded={open}
        aria-haspopup="menu"
        className={`navbar__link documentationDropdown__button${isDocsPath(pathname) ? ' navbar__link--active' : ''}`}
        onClick={() => setOpen((value) => !value)}
        onKeyDown={onButtonKeyDown}
        type="button">
        <span>{isChinese ? '文档' : 'Documentation'}</span>
        <span className="documentationDropdown__chevron" aria-hidden="true" />
      </button>
      <ul
        className={`documentationDropdown__menu${open ? ' documentationDropdown__menu--open' : ''}`}
        onKeyDown={onMenuKeyDown}
        ref={menuRef}
        role="menu">
        {versions.map((version) => (
          <li key={version.label} role="none">
            <Link
              className="documentationDropdown__item"
              onClick={() => setOpen(false)}
              role="menuitem"
              to={isChinese ? version.cnTo : version.enTo}>
              {version.label}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
