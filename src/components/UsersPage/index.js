import React from 'react';
import Layout from '@theme/Layout';
import Link from '@docusaurus/Link';
import {userCaseIssue, userCases} from '@site/src/data/users';
import {GraphField} from '@site/src/components/HomePage/GraphField';
import {
  IconBuilding,
  IconGlobe,
  IconExternal,
  IconDatabase,
  IconScale,
} from '@site/src/components/HomePage/icons';

const copy = {
  en: {
    title: 'Apache HugeGraph Users',
    description: 'Public HugeGraph user cases shared by the community.',
    eyebrow: 'Users',
    heading: 'HugeGraph User Showcase',
    lead: 'These cases come from public HugeGraph community submissions. Company logos are shown only when separately approved and available in the repository.',
    submit: 'Submit a user case',
    stats: {
      cases: 'Public cases',
      industries: 'Industries',
      backends: 'Storage backends in use',
    },
    website: 'Website',
    source: 'Source',
  },
  cn: {
    title: 'Apache HugeGraph 用户案例',
    description: '来自社区公开提交的 HugeGraph 用户案例。',
    eyebrow: '用户',
    heading: 'HugeGraph 用户案例',
    lead: '以下案例来自 HugeGraph 社区的公开提交。仅在企业另行授权并在仓库中提供素材时，本页才会展示其 Logo。',
    submit: '提交用户案例',
    stats: {
      cases: '公开案例',
      industries: '覆盖行业',
      backends: '使用的存储后端',
    },
    website: '官网',
    source: '来源',
  },
};

const INDUSTRY_CN = {
  'Knowledge Graph': '知识图谱',
  'Knowledge Q&A': '知识问答',
  'Application Metadata': '应用元数据',
  'Risk Control': '风险控制',
  'Banking Infrastructure': '银行基础设施',
  'Enterprise Relationship Graph': '企业关系图谱',
  'Games and Social Graphs': '游戏与社交图谱',
  Cybersecurity: '网络安全',
  'Network Infrastructure': '网络基础设施',
  'Public Safety': '公共安全',
  'Code Intelligence': '代码智能',
};

const REGION_CN = {
  China: '中国',
};

function localize(map, value, locale) {
  if (locale === 'cn' && value) {
    return map[value] || value;
  }
  return value;
}

function logoFallback(name) {
  return name
    .split(/\s+/)
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();
}

function splitBackends(value) {
  if (!value) {
    return [];
  }
  return value
    .split(/[,/]| and /i)
    .map((part) => part.trim())
    .filter(Boolean);
}

function isSpecified(backend) {
  return backend && !/not specified/i.test(backend);
}

function UserCaseCard({item, strings, locale}) {
  const backends = splitBackends(item.storageBackend).filter(isSpecified);
  const scenario = locale === 'cn' ? item.scenarioCn || item.scenario : item.scenario;
  const industry = localize(INDUSTRY_CN, item.industry, locale);
  const region = localize(REGION_CN, item.region, locale);
  const graphSize = locale === 'cn' ? item.graphSizeCn || item.graphSize : item.graphSize;
  return (
    <article className="hgCaseCard">
      <div className="hgCaseCard__head">
        <span className="hgCaseCard__logo" aria-hidden="true">{logoFallback(item.organization)}</span>
        <div className="hgCaseCard__heading">
          <h3 className="hgCaseCard__org">{item.organization}</h3>
          <span className="hgCaseCard__industry">{industry}</span>
        </div>
      </div>
      <p className="hgCaseCard__scenario">{scenario}</p>
      <div className="hgCaseCard__meta">
        {graphSize && (
          <span className="hgMetaPill">
            <IconScale className="hgMetaPill__icon" />
            {graphSize}
          </span>
        )}
        {backends.map((backend) => (
          <span className="hgMetaPill" key={backend}>
            <IconDatabase className="hgMetaPill__icon" />
            {backend}
          </span>
        ))}
        {region && (
          <span className="hgMetaPill hgMetaPill--ghost">
            <IconGlobe className="hgMetaPill__icon" />
            {region}
          </span>
        )}
      </div>
      <div className="hgCaseCard__links">
        {item.websiteUrl && (
          <a className="hgIconLink" href={item.websiteUrl}>
            <IconGlobe />
            {strings.website}
          </a>
        )}
        <a className="hgIconLink" href={item.sourceUrl}>
          <IconExternal />
          {strings.source}
        </a>
      </div>
    </article>
  );
}

export default function UsersPage({locale = 'en'}) {
  const strings = copy[locale];
  const industries = new Set(userCases.map((item) => item.industry));
  const backends = new Set();
  userCases.forEach((item) =>
    splitBackends(item.storageBackend).forEach((backend) => {
      if (isSpecified(backend)) {
        backends.add(backend);
      }
    }),
  );
  const stats = [
    {value: userCases.length, label: strings.stats.cases},
    {value: industries.size, label: strings.stats.industries},
    {value: backends.size, label: strings.stats.backends},
  ];

  return (
    <Layout title={strings.title} description={strings.description}>
      <header className="hgPageHero">
        <GraphField className="hgPageHero__field" sparse />
        <div className="hgPageHero__glow" aria-hidden="true" />
        <div className="container hgPageHero__inner">
          <span className="hgBadge">
            <IconBuilding className="hgBadge__icon" />
            {strings.eyebrow}
          </span>
          <h1 className="hgPageHero__title">{strings.heading}</h1>
          <p className="hgPageHero__lead">{strings.lead}</p>
          <Link className="hgBtn hgBtn--primary hgBtn--lg" href={userCaseIssue.url}>
            {strings.submit}
            <IconExternal className="hgBtn__icon" />
          </Link>
        </div>
      </header>
      <main>
        <section className="hgStats">
          <div className="container hgStats__grid hgStats__grid--3">
            {stats.map((stat) => (
              <div className="hgStat" key={stat.label}>
                <strong className="hgStat__value">{stat.value}</strong>
                <span className="hgStat__label">{stat.label}</span>
              </div>
            ))}
          </div>
        </section>
        <section className="siteBand siteBand--light">
          <div className="container">
            <div className="hgCaseGrid">
              {userCases.map((item) => (
                <UserCaseCard
                  key={`${item.organization}-${item.industry}`}
                  item={item}
                  strings={strings}
                  locale={locale}
                />
              ))}
            </div>
          </div>
        </section>
      </main>
    </Layout>
  );
}
