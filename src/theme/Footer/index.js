import React from 'react';
import Link from '@docusaurus/Link';
import {useLocation} from '@docusaurus/router';
import useBaseUrl from '@docusaurus/useBaseUrl';

/*
 * Locale-aware footer.
 *
 * The site mirrors its Chinese content under /cn/ (path-based, not Docusaurus
 * i18n), so the single-language themeConfig footer is superseded here. Column
 * titles and project/community link labels are localised for /cn/, while the
 * ASF program links and the trademark/copyright statement intentionally stay in
 * their canonical English form (ASF requirement; also asserted by the build and
 * headless UI validators).
 */

const apacheLinks = [
  {label: 'Foundation', href: 'https://www.apache.org/'},
  {label: 'License', href: 'https://www.apache.org/licenses/'},
  {label: 'Events', href: 'https://www.apache.org/events/current-event.html'},
  {label: 'Privacy', href: 'https://privacy.apache.org/policies/privacy-policy-public.html'},
  {label: 'Security', href: 'https://www.apache.org/security/'},
  {label: 'Sponsorship', href: 'https://www.apache.org/foundation/sponsorship.html'},
  {label: 'Thanks', href: 'https://www.apache.org/foundation/thanks.html'},
  {label: 'Code of Conduct', href: 'https://www.apache.org/foundation/policies/conduct.html'},
];

const content = {
  en: {
    columns: [
      {
        title: 'Project',
        items: [
          {label: 'Documentation', to: '/docs/'},
          {label: 'Download', to: '/download/'},
          {label: 'Team', to: '/team/'},
          {label: 'Users', to: '/users/'},
          {label: 'GitHub', href: 'https://github.com/apache/hugegraph'},
          {label: 'Issue Tracker', href: 'https://github.com/apache/hugegraph/issues'},
        ],
      },
      {
        title: 'Community',
        items: [
          {label: 'Community', to: '/community/'},
          {label: 'Contributor Guide', to: '/community/contribution-guidelines/'},
          {label: 'Mailing List', href: 'mailto:dev@hugegraph.apache.org'},
          {label: 'ASF Slack', href: 'https://the-asf.slack.com/archives/C059UU2FJ23'},
        ],
      },
      {title: 'ASF', items: apacheLinks},
    ],
  },
  cn: {
    columns: [
      {
        title: '项目',
        items: [
          {label: '文档', to: '/cn/docs/'},
          {label: '下载', to: '/cn/download/'},
          {label: '团队', to: '/cn/team/'},
          {label: '用户', to: '/cn/users/'},
          {label: 'GitHub', href: 'https://github.com/apache/hugegraph'},
          {label: '问题追踪', href: 'https://github.com/apache/hugegraph/issues'},
        ],
      },
      {
        title: '社区',
        items: [
          {label: '社区', to: '/cn/community/'},
          {label: '贡献指南', to: '/cn/community/contribution-guidelines/'},
          {label: '邮件列表', href: 'mailto:dev@hugegraph.apache.org'},
          {label: 'ASF Slack', href: 'https://the-asf.slack.com/archives/C059UU2FJ23'},
        ],
      },
      {title: 'ASF', items: apacheLinks},
    ],
  },
};

function FooterLink({item}) {
  return (
    <Link className="footer__link-item" {...(item.to ? {to: item.to} : {href: item.href})}>
      {item.label}
    </Link>
  );
}

export default function Footer() {
  const {pathname} = useLocation();
  const isCn = pathname === '/cn' || pathname.startsWith('/cn/');
  const data = isCn ? content.cn : content.en;
  const logoUrl = useBaseUrl('img/apache-logo.svg');
  const year = new Date().getFullYear();
  // Canonical ASF trademark statement — kept in English on every locale.
  const copyright = `Copyright © ${year} The Apache Software Foundation. Licensed under the Apache License, Version 2.0. Apache HugeGraph, HugeGraph, Apache, and related logos are trademarks of The Apache Software Foundation.`;

  return (
    <footer className="footer footer--dark">
      <div className="container container-fluid">
        <div className="row footer__links">
          {data.columns.map((col) => (
            <div className="col footer__col" key={col.title}>
              <div className="footer__title">{col.title}</div>
              <ul className="footer__items clean-list">
                {col.items.map((item) => (
                  <li className="footer__item" key={item.label}>
                    <FooterLink item={item} />
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="footer__bottom text--center">
          <div className="margin-bottom--sm">
            <a href="https://www.apache.org/" target="_blank" rel="noopener noreferrer">
              <img
                className="footer__logo"
                alt="Apache Software Foundation logo"
                src={logoUrl}
                width="180"
              />
            </a>
          </div>
          <div className="footer__copyright">{copyright}</div>
        </div>
      </div>
    </footer>
  );
}
