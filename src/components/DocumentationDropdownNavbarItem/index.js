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
  const [clickOpen, setClickOpen] = React.useState(false);
  const rootRef = React.useRef(null);
  const menuRef = React.useRef(null);
  const closeTimerRef = React.useRef(null);

  const clearCloseTimer = React.useCallback(() => {
    if (closeTimerRef.current) {
      window.clearTimeout(closeTimerRef.current);
      closeTimerRef.current = null;
    }
  }, []);

  const closeMenu = React.useCallback(() => {
    clearCloseTimer();
    setOpen(false);
    setClickOpen(false);
  }, [clearCloseTimer]);

  const openMenu = React.useCallback(() => {
    clearCloseTimer();
    setOpen(true);
  }, [clearCloseTimer]);

  const scheduleCloseMenu = React.useCallback(() => {
    clearCloseTimer();
    closeTimerRef.current = window.setTimeout(() => {
      setOpen(false);
      closeTimerRef.current = null;
    }, 180);
  }, [clearCloseTimer]);

  React.useEffect(() => {
    function closeOnOutsideClick(event) {
      if (!rootRef.current?.contains(event.target)) {
        closeMenu();
      }
    }

    document.addEventListener('mousedown', closeOnOutsideClick);
    return () => document.removeEventListener('mousedown', closeOnOutsideClick);
  }, [closeMenu]);

  React.useEffect(() => clearCloseTimer, [clearCloseTimer]);

  function onButtonKeyDown(event) {
    if (event.key === 'ArrowDown' || event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      openMenu();
      window.requestAnimationFrame(() => focusMenuItem(menuRef, 1));
    }
    if (event.key === 'Escape') {
      closeMenu();
    }
  }

  function onMenuKeyDown(event) {
    if (event.key === 'Escape') {
      closeMenu();
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
      onMouseEnter={openMenu}
      onMouseLeave={() => {
        if (!clickOpen) {
          scheduleCloseMenu();
        }
      }}
      onFocus={openMenu}>
      <button
        aria-expanded={open}
        aria-haspopup="menu"
        className={`navbar__link documentationDropdown__button${isDocsPath(pathname) ? ' navbar__link--active' : ''}`}
        onClick={() => {
          clearCloseTimer();
          if (clickOpen) {
            closeMenu();
          } else {
            setOpen(true);
            setClickOpen(true);
          }
        }}
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
              onClick={closeMenu}
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
