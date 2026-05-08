import React from 'react';
import clsx from 'clsx';
import Layout from '@theme/Layout';
import Link from '@docusaurus/Link';

const highlights = [
  {
    title: '图数据库',
    text: '面向 OLTP 场景的图存储与实时遍历，支持 REST、Gremlin 和 Cypher 访问。',
    link: '/cn/docs/quickstart/hugegraph/hugegraph-server/',
  },
  {
    title: '图计算',
    text: '通过 HugeGraph Computer 与 Vermeer 处理大规模图分析任务。',
    link: '/cn/docs/quickstart/computing/hugegraph-computer/',
  },
  {
    title: '图智能',
    text: 'GraphRAG、知识图谱构建以及图机器学习组件。',
    link: '/cn/docs/quickstart/hugegraph-ai/',
  },
];

const components = [
  ['Server', '在线图查询核心引擎'],
  ['Store / PD', '分布式存储与元数据调度'],
  ['Toolchain', 'Loader、Hubble、客户端与运维工具'],
  ['Computer', '分布式图分析与批处理'],
  ['AI', 'LLM、RAG 与图机器学习集成'],
];

function HomepageHeader() {
  return (
    <header className="hugegraphHero">
      <div className="hugegraphHero__overlay" />
      <div className="hugegraphHero__content">
        <p className="apacheEyebrow">Apache Software Foundation Project</p>
        <h1>Apache HugeGraph</h1>
        <p className="hugegraphHero__lead">
          面向实时图查询、大规模图分析和 AI 应用的全栈图数据库生态系统。
        </p>
        <div className="hugegraphHero__actions">
          <Link className="button button--primary button--lg" to="/cn/docs/">
            阅读文档
          </Link>
          <Link className="button button--secondary button--lg" to="/cn/download/">
            下载
          </Link>
        </div>
      </div>
    </header>
  );
}

function Highlights() {
  return (
    <section className="siteBand siteBand--light">
      <div className="container">
        <div className="sectionHeading">
          <p className="apacheEyebrow">文档入口</p>
          <h2>从你需要的技术栈开始</h2>
        </div>
        <div className="highlightGrid">
          {highlights.map((item) => (
            <article className="productCard" key={item.title}>
              <h3>{item.title}</h3>
              <p>{item.text}</p>
              <Link to={item.link}>打开指南</Link>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

function Ecosystem() {
  return (
    <section className="siteBand">
      <div className="container ecosystemLayout">
        <div>
          <p className="apacheEyebrow">HugeGraph 生态</p>
          <h2>覆盖完整项目族的一站式文档</h2>
          <p>
            新站点保留 HugeGraph Server、Store、PD、Toolchain、Computer 与 AI
            文档，并提供中英文导航。
          </p>
          <Link className="button button--outline button--primary" to="/cn/community/">
            社区
          </Link>
        </div>
        <div className="ecosystemMap" aria-label="HugeGraph ecosystem components">
          {components.map(([name, text], index) => (
            <div className={clsx('ecosystemNode', `ecosystemNode--${index + 1}`)} key={name}>
              <strong>{name}</strong>
              <span>{text}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export default function HomeCn() {
  return (
    <Layout title="Apache HugeGraph" description="Apache HugeGraph 中文文档。">
      <HomepageHeader />
      <main>
        <Highlights />
        <Ecosystem />
      </main>
    </Layout>
  );
}
