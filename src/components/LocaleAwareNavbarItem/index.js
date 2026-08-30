import React from 'react';
import {useLocation} from '@docusaurus/router';
import DefaultNavbarItem from '@theme/NavbarItem/DefaultNavbarItem';

function isChinesePath(pathname) {
  return pathname === '/cn' || pathname.startsWith('/cn/');
}

export default function LocaleAwareNavbarItem({
  enTo,
  cnTo,
  cnLabel,
  cnActiveBasePath,
  label,
  activeBasePath,
  ...props
}) {
  const {pathname} = useLocation();
  const isChinese = isChinesePath(pathname);

  return (
    <DefaultNavbarItem
      {...props}
      label={isChinese ? cnLabel || label : label}
      to={isChinese ? cnTo : enTo}
      activeBasePath={isChinese ? cnActiveBasePath || cnTo : activeBasePath || enTo}
    />
  );
}
