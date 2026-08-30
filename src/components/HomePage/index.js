import React from 'react';
import Layout from '@theme/Layout';
import Link from '@docusaurus/Link';
import {
  IconDatabase,
  IconCompute,
  IconAI,
  IconApi,
  IconQuery,
  IconDistributed,
  IconVisualize,
  IconScale,
  IconArrowRight,
  IconGithub,
  IconSpark,
  IconBook,
} from './icons';
import {GraphField} from './GraphField';
import {TerminalBlock} from './TerminalBlock';

const copy = {
  en: {
    docs: '/docs/',
    quickstart: '/docs/quickstart/',
    download: '/download/',
    community: '/community/',
    github: 'https://github.com/apache/hugegraph',
    meta: {
      title: 'Apache HugeGraph',
      description:
        'Apache HugeGraph is a full-stack graph database ecosystem for OLTP, OLAP, and graph AI — fast real-time traversals, distributed analytics, and GraphRAG.',
    },
    copyLabel: 'Copy',
    copiedLabel: 'Copied',
    hero: {
      badge: 'Apache Software Foundation · Top-Level Project',
      title: 'Apache HugeGraph',
      lead: 'A full-stack graph database ecosystem for real-time graph queries, large-scale graph analytics, and AI-native applications — open source under the Apache License 2.0.',
      primary: 'Get Started',
      secondary: 'View on GitHub',
      terminalTitle: 'quick-start.sh',
    },
    stats: [
      ['OLTP · OLAP · AI', 'One unified graph stack'],
      ['100B+', 'Vertices & edges at scale'],
      ['REST · Gremlin · Cypher', 'Familiar query access'],
      ['Apache TLP', 'Open governance & community'],
    ],
    highlightsTitle: 'Start from the part of the stack you need',
    highlightsEyebrow: 'Documentation entry points',
    highlights: [
      {
        icon: IconDatabase,
        title: 'Graph Database',
        text: 'OLTP graph storage and real-time multi-hop traversal with REST, Gremlin, and Cypher access paths.',
        link: '/docs/quickstart/hugegraph/hugegraph-server/',
        cta: 'Open server guide',
      },
      {
        icon: IconCompute,
        title: 'Graph Computing',
        text: 'OLAP processing for very large graphs through HugeGraph Computer and the Vermeer engine.',
        link: '/docs/quickstart/computing/hugegraph-computer/',
        cta: 'Open computing guide',
      },
      {
        icon: IconAI,
        title: 'Graph AI',
        text: 'GraphRAG, knowledge-graph construction, and graph machine-learning components for LLM apps.',
        link: '/docs/quickstart/hugegraph-ai/',
        cta: 'Open AI guide',
      },
    ],
    capsEyebrow: 'Why HugeGraph',
    capsTitle: 'Built for production graph workloads',
    caps: [
      {icon: IconApi, title: 'REST & RPC APIs', text: 'A complete HTTP API surface plus high-performance clients for Java, Python, Go, and Node.js.'},
      {icon: IconQuery, title: 'Multiple query languages', text: 'Apache TinkerPop Gremlin and Cypher over the same graph, with rich traversal and path algorithms.'},
      {icon: IconDistributed, title: 'Pluggable storage', text: 'Run on RocksDB, HBase, Cassandra, MySQL, or the distributed HugeGraph Store with PD scheduling.'},
      {icon: IconVisualize, title: 'Visual exploration', text: 'HugeGraph Hubble provides schema management, data import, and interactive graph analysis in the browser.'},
      {icon: IconCompute, title: 'Large-scale analytics', text: 'Distributed OLAP algorithms — PageRank, community detection, shortest path — over billion-edge graphs.'},
      {icon: IconScale, title: 'Scales with you', text: 'From a single embedded instance to a distributed cluster, with online schema changes and backups.'},
    ],
    quickstartEyebrow: 'Quick start',
    quickstartTitle: 'From zero to a running graph in minutes',
    quickstartText: 'Spin up HugeGraph Server with Docker, then explore it with the built-in Gremlin console or Hubble UI. The documentation walks through every backend and deployment mode.',
    quickstartCta: 'Read the quick start',
    ecoEyebrow: 'HugeGraph ecosystem',
    ecoTitle: 'One documentation home for the full project family',
    ecoText: 'Server, Store, PD, Toolchain, Computer, and AI — the whole stack documented together with bilingual navigation and versioned releases.',
    ecoCommunity: 'Meet the community',
    ecoLayers: [
      {label: 'Access', items: ['REST API', 'Gremlin', 'Cypher', 'Clients']},
      {label: 'Compute & serve', items: ['HugeGraph Server', 'Computer / Vermeer', 'HugeGraph AI']},
      {label: 'Storage', items: ['HugeGraph Store', 'PD', 'RocksDB · HBase · Cassandra']},
      {label: 'Operate', items: ['Hubble', 'Loader', 'Tools']},
    ],
    ctaTitle: 'Ready to build with graphs?',
    ctaText: 'Dive into the documentation, download a release, or join the Apache HugeGraph community.',
    ctaPrimary: 'Read the docs',
    ctaSecondary: 'Download',
  },
  cn: {
    docs: '/cn/docs/',
    quickstart: '/cn/docs/quickstart/',
    download: '/cn/download/',
    community: '/cn/community/',
    github: 'https://github.com/apache/hugegraph',
    meta: {
      title: 'Apache HugeGraph',
      description:
        'Apache HugeGraph 是面向 OLTP、OLAP 与图智能的全栈图数据库生态：实时图遍历、分布式图分析与 GraphRAG。',
    },
    copyLabel: '复制',
    copiedLabel: '已复制',
    hero: {
      badge: 'Apache 软件基金会 · 顶级项目',
      title: 'Apache HugeGraph',
      lead: '面向实时图查询、大规模图分析和 AI 原生应用的全栈图数据库生态系统，基于 Apache License 2.0 开源。',
      primary: '开始使用',
      secondary: '在 GitHub 上查看',
      terminalTitle: 'quick-start.sh',
    },
    stats: [
      ['OLTP · OLAP · AI', '统一的图技术栈'],
      ['百亿级+', '顶点与边的规模'],
      ['REST · Gremlin · Cypher', '熟悉的查询方式'],
      ['Apache 顶级项目', '开放治理与社区'],
    ],
    highlightsTitle: '从你需要的技术栈开始',
    highlightsEyebrow: '文档入口',
    highlights: [
      {
        icon: IconDatabase,
        title: '图数据库',
        text: '面向 OLTP 场景的图存储与实时多跳遍历，支持 REST、Gremlin 和 Cypher 访问。',
        link: '/cn/docs/quickstart/hugegraph/hugegraph-server/',
        cta: '查看 Server 指南',
      },
      {
        icon: IconCompute,
        title: '图计算',
        text: '通过 HugeGraph Computer 与 Vermeer 引擎处理超大规模图分析任务。',
        link: '/cn/docs/quickstart/computing/hugegraph-computer/',
        cta: '查看计算指南',
      },
      {
        icon: IconAI,
        title: '图智能',
        text: '面向 LLM 应用的 GraphRAG、知识图谱构建与图机器学习组件。',
        link: '/cn/docs/quickstart/hugegraph-ai/',
        cta: '查看 AI 指南',
      },
    ],
    capsEyebrow: '为什么选择 HugeGraph',
    capsTitle: '为生产级图工作负载打造',
    caps: [
      {icon: IconApi, title: 'REST 与 RPC 接口', text: '完整的 HTTP API，以及 Java、Python、Go、Node.js 的高性能客户端。'},
      {icon: IconQuery, title: '多种查询语言', text: '在同一张图上使用 Apache TinkerPop Gremlin 与 Cypher，内置丰富的遍历与路径算法。'},
      {icon: IconDistributed, title: '可插拔存储', text: '支持 RocksDB、HBase、Cassandra、MySQL，以及带 PD 调度的分布式 HugeGraph Store。'},
      {icon: IconVisualize, title: '可视化探索', text: 'HugeGraph Hubble 提供 Schema 管理、数据导入与浏览器内的交互式图分析。'},
      {icon: IconCompute, title: '大规模分析', text: '面向十亿级边的分布式 OLAP 算法：PageRank、社区发现、最短路径等。'},
      {icon: IconScale, title: '弹性伸缩', text: '从单机嵌入式到分布式集群，支持在线 Schema 变更与备份。'},
    ],
    quickstartEyebrow: '快速开始',
    quickstartTitle: '几分钟即可运行你的第一张图',
    quickstartText: '使用 Docker 启动 HugeGraph Server，再用内置 Gremlin 控制台或 Hubble 界面进行探索。文档覆盖每种存储后端与部署模式。',
    quickstartCta: '阅读快速开始',
    ecoEyebrow: 'HugeGraph 生态',
    ecoTitle: '一站式文档，覆盖完整项目生态',
    ecoText: 'Server、Store、PD、Toolchain、Computer 与 AI —— 整套技术栈的文档汇聚一处，提供中英文导航与版本化发布。',
    ecoCommunity: '了解社区',
    ecoLayers: [
      {label: '访问层', items: ['REST API', 'Gremlin', 'Cypher', '客户端']},
      {label: '计算与服务', items: ['HugeGraph Server', 'Computer / Vermeer', 'HugeGraph AI']},
      {label: '存储层', items: ['HugeGraph Store', 'PD', 'RocksDB · HBase · Cassandra']},
      {label: '运维工具', items: ['Hubble', 'Loader', 'Tools']},
    ],
    ctaTitle: '准备好开始构建图应用了吗？',
    ctaText: '深入阅读文档、下载发布版本，或加入 Apache HugeGraph 社区。',
    ctaPrimary: '阅读文档',
    ctaSecondary: '下载',
  },
};

const quickstartLines = [
  {type: 'comment', text: '# 1. Start HugeGraph Server with Docker'},
  {type: 'cmd', text: 'docker run -d --name=hugegraph -p 8080:8080 hugegraph/hugegraph'},
  {type: 'blank', text: ''},
  {type: 'comment', text: '# 2. Check the server is up via the REST API'},
  {type: 'cmd', text: 'curl -s http://localhost:8080/apis/version'},
  {type: 'blank', text: ''},
  {type: 'comment', text: '# 3. Explore visually with HugeGraph Hubble'},
  {type: 'cmd', text: 'docker run -d --name=hubble -p 8088:8088 hugegraph/hubble'},
];

const quickstartPlain = quickstartLines
  .map((line) => line.text)
  .join('\n')
  .replace(/\n{2,}/g, '\n\n');

function HomeHero({c}) {
  return (
    <header className="hgHero">
      <GraphField className="hgHero__field" />
      <div className="hgHero__glow" aria-hidden="true" />
      <div className="container hgHero__inner">
        <div className="hgHero__copy">
          <span className="hgBadge">
            <IconSpark className="hgBadge__icon" />
            {c.hero.badge}
          </span>
          <h1 className="hgHero__title">{c.hero.title}</h1>
          <p className="hgHero__lead">{c.hero.lead}</p>
          <div className="hgHero__actions">
            <Link className="hgBtn hgBtn--primary hgBtn--lg" to={c.docs}>
              {c.hero.primary}
              <IconArrowRight className="hgBtn__icon" />
            </Link>
            <Link className="hgBtn hgBtn--ghost hgBtn--lg" href={c.github}>
              <IconGithub className="hgBtn__icon hgBtn__icon--lead" />
              {c.hero.secondary}
            </Link>
          </div>
        </div>
        <div className="hgHero__panel">
          <TerminalBlock
            title={c.hero.terminalTitle}
            lines={quickstartLines}
            plain={quickstartPlain}
            copyLabel={c.copyLabel}
            copiedLabel={c.copiedLabel}
          />
        </div>
      </div>
    </header>
  );
}

function StatsStrip({c}) {
  return (
    <section className="hgStats">
      <div className="container hgStats__grid">
        {c.stats.map(([value, label]) => (
          <div className="hgStat" key={label}>
            <strong className="hgStat__value">{value}</strong>
            <span className="hgStat__label">{label}</span>
          </div>
        ))}
      </div>
    </section>
  );
}

function Highlights({c}) {
  return (
    <section className="siteBand siteBand--light">
      <div className="container">
        <div className="sectionHeading">
          <p className="apacheEyebrow">{c.highlightsEyebrow}</p>
          <h2>{c.highlightsTitle}</h2>
        </div>
        <div className="highlightGrid">
          {c.highlights.map((item) => {
            const Icon = item.icon;
            return (
              <article className="productCard productCard--feature" key={item.title}>
                <span className="hgFeatureIcon" aria-hidden="true">
                  <Icon />
                </span>
                <h3>{item.title}</h3>
                <p>{item.text}</p>
                <Link className="hgCardLink" to={item.link}>
                  {item.cta}
                  <IconArrowRight className="hgCardLink__icon" />
                </Link>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}

function Capabilities({c}) {
  return (
    <section className="siteBand">
      <div className="container">
        <div className="sectionHeading">
          <p className="apacheEyebrow">{c.capsEyebrow}</p>
          <h2>{c.capsTitle}</h2>
        </div>
        <div className="hgCapGrid">
          {c.caps.map((item) => {
            const Icon = item.icon;
            return (
              <article className="hgCapCard" key={item.title}>
                <span className="hgCapCard__icon" aria-hidden="true">
                  <Icon />
                </span>
                <div>
                  <h3>{item.title}</h3>
                  <p>{item.text}</p>
                </div>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}

function QuickStart({c}) {
  return (
    <section className="siteBand siteBand--light">
      <div className="container hgQuickstart">
        <div className="hgQuickstart__copy">
          <p className="apacheEyebrow">{c.quickstartEyebrow}</p>
          <h2>{c.quickstartTitle}</h2>
          <p>{c.quickstartText}</p>
          <Link className="hgBtn hgBtn--primary" to={c.quickstart}>
            <IconBook className="hgBtn__icon hgBtn__icon--lead" />
            {c.quickstartCta}
          </Link>
        </div>
        <div className="hgQuickstart__code">
          <TerminalBlock
            title="bash"
            lines={quickstartLines}
            plain={quickstartPlain}
            copyLabel={c.copyLabel}
            copiedLabel={c.copiedLabel}
          />
        </div>
      </div>
    </section>
  );
}

function Ecosystem({c}) {
  return (
    <section className="siteBand">
      <div className="container ecosystemLayout">
        <div>
          <p className="apacheEyebrow">{c.ecoEyebrow}</p>
          <h2>{c.ecoTitle}</h2>
          <p>{c.ecoText}</p>
          <Link className="hgBtn hgBtn--outline" to={c.community}>
            {c.ecoCommunity}
            <IconArrowRight className="hgBtn__icon" />
          </Link>
        </div>
        <div className="hgStack" aria-label="HugeGraph architecture layers">
          {c.ecoLayers.map((layer) => (
            <div className="hgStackLayer" key={layer.label}>
              <span className="hgStackLayer__label">{layer.label}</span>
              <div className="hgStackLayer__items">
                {layer.items.map((item) => (
                  <span className="hgChip" key={item}>
                    {item}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function FinalCta({c}) {
  return (
    <section className="hgCta">
      <GraphField className="hgCta__field" sparse />
      <div className="container hgCta__inner">
        <h2 className="hgCta__title">{c.ctaTitle}</h2>
        <p className="hgCta__text">{c.ctaText}</p>
        <div className="hgCta__actions">
          <Link className="hgBtn hgBtn--primary hgBtn--lg" to={c.docs}>
            {c.ctaPrimary}
            <IconArrowRight className="hgBtn__icon" />
          </Link>
          <Link className="hgBtn hgBtn--ghost hgBtn--lg" to={c.download}>
            {c.ctaSecondary}
          </Link>
        </div>
      </div>
    </section>
  );
}

export default function HomePage({locale = 'en'}) {
  const c = copy[locale] || copy.en;
  return (
    <Layout title={c.meta.title} description={c.meta.description}>
      <HomeHero c={c} />
      <main>
        <StatsStrip c={c} />
        <Highlights c={c} />
        <Capabilities c={c} />
        <QuickStart c={c} />
        <Ecosystem c={c} />
        <FinalCta c={c} />
      </main>
    </Layout>
  );
}
