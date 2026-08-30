import React from 'react';
import Layout from '@theme/Layout';
import Link from '@docusaurus/Link';
import {userCaseIssue, userCases} from '@site/src/data/users';

const copy = {
  en: {
    title: 'Apache HugeGraph Users',
    description: 'Public HugeGraph user cases shared by the community.',
    eyebrow: 'Users',
    heading: 'HugeGraph User Showcase',
    lead: 'These cases come from public HugeGraph community submissions. Logos are intentionally omitted unless separately approved and available in the repository.',
    submit: 'Submit a user case',
    industry: 'Industry',
    storage: 'Storage',
    graphSize: 'Graph size',
    website: 'Website',
    source: 'Source',
    noLogo: 'No logo',
  },
  cn: {
    title: 'Apache HugeGraph 用户案例',
    description: '来自社区公开提交的 HugeGraph 用户案例。',
    eyebrow: '用户',
    heading: 'HugeGraph 用户案例',
    lead: '这些案例来自 HugeGraph 社区公开提交。除非仓库中已有明确授权的素材，本页不展示公司 Logo。',
    submit: '提交用户案例',
    industry: '行业',
    storage: '存储后端',
    graphSize: '图规模',
    website: '官网',
    source: '来源',
    noLogo: '无 Logo',
  },
};

function groupByIndustry(cases) {
  return cases.reduce((groups, item) => {
    const industry = item.industry || 'Other';
    if (!groups.has(industry)) {
      groups.set(industry, []);
    }
    groups.get(industry).push(item);
    return groups;
  }, new Map());
}

function logoFallback(name) {
  return name
    .split(/\s+/)
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();
}

function UserCaseCard({item, strings, locale}) {
  return (
    <article className="showcaseCard">
      <div className="showcaseLogo" aria-label={strings.noLogo}>{logoFallback(item.organization)}</div>
      <div>
        <h3>{item.organization}</h3>
        <p>{locale === 'cn' ? item.scenarioCn || item.scenario : item.scenario}</p>
        <dl className="metadataList">
          <div>
            <dt>{strings.industry}</dt>
            <dd>{item.industry}</dd>
          </div>
          {item.storageBackend && (
            <div>
              <dt>{strings.storage}</dt>
              <dd>{item.storageBackend}</dd>
            </div>
          )}
          {item.graphSize && (
            <div>
              <dt>{strings.graphSize}</dt>
              <dd>{item.graphSize}</dd>
            </div>
          )}
        </dl>
        <div className="inlineLinks">
          {item.websiteUrl && <a href={item.websiteUrl}>{strings.website}</a>}
          <a href={item.sourceUrl}>{strings.source}</a>
        </div>
      </div>
    </article>
  );
}

export default function UsersPage({locale = 'en'}) {
  const strings = copy[locale];
  const groupedCases = Array.from(groupByIndustry(userCases).entries());

  return (
    <Layout title={strings.title} description={strings.description}>
      <header className="subpageHero">
        <div className="container">
          <p className="apacheEyebrow">{strings.eyebrow}</p>
          <h1>{strings.heading}</h1>
          <p>{strings.lead}</p>
          <Link className="button button--primary" to={userCaseIssue.url}>
            {strings.submit}
          </Link>
        </div>
      </header>
      <main>
        {groupedCases.map(([industry, cases], index) => (
          <section className={index % 2 === 0 ? 'siteBand siteBand--light' : 'siteBand'} key={industry}>
            <div className="container">
              <div className="sectionHeading">
                <p className="apacheEyebrow">{strings.industry}</p>
                <h2>{industry}</h2>
              </div>
              <div className="showcaseGrid">
                {cases.map((item) => (
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
        ))}
      </main>
    </Layout>
  );
}
