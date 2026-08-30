import React from 'react';
import Layout from '@theme/Layout';
import Link from '@docusaurus/Link';
import {contributorLinks, teamMembers, teamSources} from '@site/src/data/team';

const copy = {
  en: {
    title: 'Apache HugeGraph Team',
    description: 'Project members, committers, and contributor entry points for Apache HugeGraph.',
    eyebrow: 'Community',
    heading: 'Apache HugeGraph Team',
    lead: 'HugeGraph is maintained by an Apache project community. This page is generated from local data sourced from public ASF roster information.',
    pmc: 'PMC Members',
    committers: 'Committers',
    contributors: 'Contributors',
    mapTitle: 'Contributor Map',
    mapLead: 'The community is represented here by responsibility groups instead of a heavy runtime map library.',
    sources: 'Data Sources',
    addNote: 'New contributors are added through the Apache community process. Start with the contribution guide and GitHub contributor history.',
    profile: 'Apache profile',
    homepage: 'Homepage',
  },
  cn: {
    title: 'Apache HugeGraph 团队',
    description: 'Apache HugeGraph 的项目成员、Committer 和贡献入口。',
    eyebrow: '社区',
    heading: 'Apache HugeGraph 团队',
    lead: 'HugeGraph 由 Apache 项目社区维护。本页面使用来自 ASF 公开 roster 的本地数据生成。',
    pmc: 'PMC 成员',
    committers: 'Committers',
    contributors: '贡献者',
    mapTitle: '贡献者地图',
    mapLead: '这里用职责分组呈现社区分布，避免引入较重的运行时地图依赖。',
    sources: '数据来源',
    addNote: '新的贡献者通过 Apache 社区流程加入。可以从贡献指南和 GitHub 贡献历史开始。',
    profile: 'Apache 资料',
    homepage: '主页',
  },
};

function initials(name) {
  return name
    .split(/\s+/)
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();
}

function apacheProfile(apacheId) {
  return `https://people.apache.org/committer-index.html#${apacheId}`;
}

function MemberCard({member, strings}) {
  return (
    <article className="directoryCard">
      <div className="directoryAvatar" aria-hidden="true">{initials(member.name)}</div>
      <div>
        <h3>{member.name}</h3>
        <p>{member.role}</p>
        <div className="inlineLinks">
          <a href={apacheProfile(member.apacheId)}>{strings.profile}</a>
          {member.homepage && <a href={member.homepage}>{strings.homepage}</a>}
        </div>
      </div>
    </article>
  );
}

function MemberSection({title, members, strings}) {
  return (
    <section className="siteBand">
      <div className="container">
        <div className="sectionHeading">
          <h2>{title}</h2>
        </div>
        <div className="directoryGrid">
          {members.map((member) => (
            <MemberCard key={member.apacheId} member={member} strings={strings} />
          ))}
        </div>
      </div>
    </section>
  );
}

export default function TeamPage({locale = 'en'}) {
  const strings = copy[locale];
  const pmcMembers = teamMembers.filter((member) => member.groups.includes('pmc'));
  const committers = teamMembers.filter((member) => !member.groups.includes('pmc'));
  const contributorStats = [
    {label: strings.pmc, value: pmcMembers.length},
    {label: strings.committers, value: teamMembers.length},
    {label: strings.contributors, value: 'GitHub'},
  ];

  return (
    <Layout title={strings.title} description={strings.description}>
      <header className="subpageHero">
        <div className="container">
          <p className="apacheEyebrow">{strings.eyebrow}</p>
          <h1>{strings.heading}</h1>
          <p>{strings.lead}</p>
        </div>
      </header>
      <main>
        <section className="siteBand siteBand--light">
          <div className="container">
            <div className="sectionHeading">
              <h2>{strings.mapTitle}</h2>
              <p>{strings.mapLead}</p>
            </div>
            <div className="statGrid">
              {contributorStats.map((item) => (
                <div className="statCard" key={item.label}>
                  <strong>{item.value}</strong>
                  <span>{item.label}</span>
                </div>
              ))}
            </div>
          </div>
        </section>
        <MemberSection title={strings.pmc} members={pmcMembers} strings={strings} />
        <MemberSection title={strings.committers} members={committers} strings={strings} />
        <section className="siteBand siteBand--light">
          <div className="container">
            <div className="sectionHeading">
              <h2>{strings.contributors}</h2>
              <p>{strings.addNote}</p>
            </div>
            <div className="linkGrid">
              {contributorLinks.map((link) => (
                <Link className="linkCard" key={link.url} to={link.url}>
                  {link.label}
                </Link>
              ))}
            </div>
            <h3>{strings.sources}</h3>
            <ul>
              {teamSources.map((source) => (
                <li key={source.url}>
                  <a href={source.url}>{source.label}</a>
                </li>
              ))}
            </ul>
          </div>
        </section>
      </main>
    </Layout>
  );
}
