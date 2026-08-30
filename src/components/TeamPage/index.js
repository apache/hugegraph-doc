import React from 'react';
import clsx from 'clsx';
import Layout from '@theme/Layout';
import Link from '@docusaurus/Link';
import {contributorLinks, teamMembers, teamSources} from '@site/src/data/team';
import {GraphField} from '@site/src/components/HomePage/GraphField';
import {
  IconUsers,
  IconCommit,
  IconGithub,
  IconArrowRight,
  IconGlobe,
  IconExternal,
} from '@site/src/components/HomePage/icons';

const copy = {
  en: {
    title: 'Apache HugeGraph Team',
    description: 'Project members, committers, and contributor entry points for Apache HugeGraph.',
    eyebrow: 'Community',
    heading: 'Apache HugeGraph Team',
    lead: 'HugeGraph is built and maintained by an open Apache project community. This page is generated from public ASF roster data.',
    metricsTitle: 'The community at a glance',
    metricsLead: 'Members are grouped by their role in the project.',
    pmc: 'PMC Members',
    committers: 'Committers',
    contributors: 'Contributors',
    contributorsValue: 'Open',
    contributeTitle: 'Become a contributor',
    contributeLead: 'New contributors join through the Apache community process — start with the contribution guide and the GitHub contributor history.',
    sources: 'Data sources',
    profile: 'Apache profile',
    homepage: 'Homepage',
  },
  cn: {
    title: 'Apache HugeGraph 团队',
    description: 'Apache HugeGraph 的项目成员、Committer 和参与方式。',
    eyebrow: '社区',
    heading: 'Apache HugeGraph 团队',
    lead: 'HugeGraph 由开放的 Apache 项目社区共同构建和维护，本页面根据 ASF 公开的成员名册数据生成。',
    metricsTitle: '社区概览',
    metricsLead: '按成员在项目中的职责进行分组展示。',
    pmc: 'PMC 成员',
    committers: 'Committer',
    contributors: '贡献者',
    contributorsValue: '开放',
    contributeTitle: '成为贡献者',
    contributeLead: '新的贡献者通过 Apache 社区流程加入，可以从贡献指南和 GitHub 贡献记录开始。',
    sources: '数据来源',
    profile: 'Apache 主页',
    homepage: '个人主页',
  },
};

const roleLabelsCn = {
  'PMC Chair': 'PMC 主席',
  'PMC Member': 'PMC 成员',
  Committer: 'Committer',
};

const contributorLinkLabelsCn = {
  'HugeGraph contributors': 'HugeGraph 贡献者',
  'Documentation contributors': '文档贡献者',
  'Contribution guide': '贡献指南',
};

const sourceLabelsCn = {
  'ASF Committee Info': 'ASF 委员会信息',
  'ASF LDAP Project Roster': 'ASF LDAP 项目名册',
  'ASF Public People Data': 'ASF 公开人员数据',
};

function localizeLink(label, locale) {
  if (locale === 'cn') {
    return contributorLinkLabelsCn[label] || label;
  }
  return label;
}

function localizeSource(label, locale) {
  if (locale === 'cn') {
    return sourceLabelsCn[label] || label;
  }
  return label;
}

function roleLabel(role, locale) {
  if (locale === 'cn') {
    return roleLabelsCn[role] || role;
  }
  return role;
}

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

function roleClass(role) {
  if (/chair/i.test(role)) {
    return 'hgRoleBadge--chair';
  }
  if (/pmc/i.test(role)) {
    return 'hgRoleBadge--pmc';
  }
  return 'hgRoleBadge--committer';
}

function MemberCard({member, strings, locale}) {
  return (
    <article className="hgMemberCard">
      <div className="hgMemberCard__top">
        <span className="hgMemberCard__avatar" aria-hidden="true">{initials(member.name)}</span>
        <span className={clsx('hgRoleBadge', roleClass(member.role))}>{roleLabel(member.role, locale)}</span>
      </div>
      <h3 className="hgMemberCard__name">{member.name}</h3>
      <p className="hgMemberCard__id">@{member.apacheId}</p>
      <div className="hgMemberCard__links">
        <a className="hgIconLink" href={apacheProfile(member.apacheId)}>
          <IconExternal />
          {strings.profile}
        </a>
        {member.homepage && (
          <a className="hgIconLink" href={member.homepage}>
            <IconGlobe />
            {strings.homepage}
          </a>
        )}
      </div>
    </article>
  );
}

function MemberSection({title, members, strings, locale, light}) {
  return (
    <section className={clsx('siteBand', light && 'siteBand--light')}>
      <div className="container">
        <div className="sectionHeading">
          <h2>{title}</h2>
        </div>
        <div className="hgMemberGrid">
          {members.map((member) => (
            <MemberCard key={member.apacheId} member={member} strings={strings} locale={locale} />
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
  const metrics = [
    {icon: IconUsers, value: pmcMembers.length, label: strings.pmc},
    {icon: IconCommit, value: teamMembers.length, label: strings.committers},
    {icon: IconGithub, value: strings.contributorsValue, label: strings.contributors},
  ];

  return (
    <Layout title={strings.title} description={strings.description}>
      <header className="hgPageHero">
        <GraphField className="hgPageHero__field" sparse />
        <div className="hgPageHero__glow" aria-hidden="true" />
        <div className="container hgPageHero__inner">
          <span className="hgBadge">
            <IconUsers className="hgBadge__icon" />
            {strings.eyebrow}
          </span>
          <h1 className="hgPageHero__title">{strings.heading}</h1>
          <p className="hgPageHero__lead">{strings.lead}</p>
        </div>
      </header>
      <main>
        <section className="siteBand siteBand--light">
          <div className="container">
            <div className="sectionHeading">
              <h2>{strings.metricsTitle}</h2>
              <p>{strings.metricsLead}</p>
            </div>
            <div className="hgMetricGrid">
              {metrics.map((metric) => {
                const Icon = metric.icon;
                return (
                  <div className="hgMetric" key={metric.label}>
                    <span className="hgMetric__icon" aria-hidden="true">
                      <Icon />
                    </span>
                    <strong className="hgMetric__value">{metric.value}</strong>
                    <span className="hgMetric__label">{metric.label}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </section>
        <MemberSection title={strings.pmc} members={pmcMembers} strings={strings} locale={locale} />
        <MemberSection title={strings.committers} members={committers} strings={strings} locale={locale} light />
        <section className="siteBand">
          <div className="container">
            <div className="sectionHeading">
              <h2>{strings.contributeTitle}</h2>
              <p>{strings.contributeLead}</p>
            </div>
            <div className="hgLinkGrid">
              {contributorLinks.map((link) => (
                <Link className="hgLinkCard" key={link.url} to={link.url}>
                  <span>{localizeLink(link.label, locale)}</span>
                  <IconArrowRight className="hgLinkCard__icon" />
                </Link>
              ))}
            </div>
            <p className="hgSourcesTitle">{strings.sources}</p>
            <div className="hgSources">
              {teamSources.map((source) => (
                <a className="hgChip hgChip--link" href={source.url} key={source.url}>
                  {localizeSource(source.label, locale)}
                </a>
              ))}
            </div>
          </div>
        </section>
      </main>
    </Layout>
  );
}
