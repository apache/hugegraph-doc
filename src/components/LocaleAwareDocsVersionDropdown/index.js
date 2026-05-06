import React from 'react';
import {useLocation} from '@docusaurus/router';
import DocsVersionDropdownNavbarItem from '@theme/NavbarItem/DocsVersionDropdownNavbarItem';

function isChinesePath(pathname) {
  return pathname === '/cn' || pathname.startsWith('/cn/');
}

export default function LocaleAwareDocsVersionDropdown(props) {
  const {pathname} = useLocation();
  const isChinese = isChinesePath(pathname);

  return (
    <DocsVersionDropdownNavbarItem
      {...props}
      docsPluginId={isChinese ? 'docs-cn' : undefined}
      dropdownItemsBefore={props.dropdownItemsBefore ?? []}
      dropdownItemsAfter={props.dropdownItemsAfter ?? []}
      label={isChinese ? '版本' : 'Version'}
    />
  );
}
