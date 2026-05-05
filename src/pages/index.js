import React from 'react';
import clsx from 'clsx';
import Layout from '@theme/Layout';
import Link from '@docusaurus/Link';

const highlights = [
  {
    title: 'Graph Database',
    text: 'OLTP graph storage and real-time traversal with REST, Gremlin, and Cypher access paths.',
    link: '/docs/quickstart/hugegraph/hugegraph-server/',
  },
  {
    title: 'Graph Computing',
    text: 'OLAP processing for large graphs through HugeGraph Computer and Vermeer.',
    link: '/docs/quickstart/computing/hugegraph-computer/',
  },
  {
    title: 'Graph AI',
    text: 'GraphRAG, knowledge graph construction, and graph machine learning components.',
    link: '/docs/quickstart/hugegraph-ai/',
  },
];

const components = [
  ['Server', 'Core graph engine for online graph queries'],
  ['Store / PD', 'Distributed storage and placement metadata'],
  ['Toolchain', 'Loader, Hubble, clients, and operational tools'],
  ['Computer', 'Distributed graph analytics and batch processing'],
  ['AI', 'LLM, RAG, and graph ML integrations'],
];

function HomepageHeader() {
  return (
    <header className="hugegraphHero">
      <div className="hugegraphHero__overlay" />
      <div className="hugegraphHero__content">
        <p className="apacheEyebrow">Apache Software Foundation Project</p>
        <h1>Apache HugeGraph</h1>
        <p className="hugegraphHero__lead">
          A full-stack graph database ecosystem for real-time graph queries,
          large-scale graph analytics, and AI applications.
        </p>
        <div className="hugegraphHero__actions">
          <Link className="button button--primary button--lg" to="/docs/">
            Read Documentation
          </Link>
          <Link className="button button--secondary button--lg" to="/docs/download/download/">
            Download
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
          <p className="apacheEyebrow">Documentation Entry Points</p>
          <h2>Start from the part of the stack you need</h2>
        </div>
        <div className="highlightGrid">
          {highlights.map((item) => (
            <article className="productCard" key={item.title}>
              <h3>{item.title}</h3>
              <p>{item.text}</p>
              <Link to={item.link}>Open guide</Link>
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
          <p className="apacheEyebrow">HugeGraph Ecosystem</p>
          <h2>One documentation home for the full project family</h2>
          <p>
            The site keeps the existing HugeGraph Server, Store, PD, Toolchain,
            Computer, and AI documentation together with bilingual navigation.
          </p>
          <Link className="button button--outline button--primary" to="/community/">
            Community
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

export default function Home() {
  return (
    <Layout
      title="Apache HugeGraph"
      description="Apache HugeGraph documentation for graph database, graph computing, and graph AI.">
      <HomepageHeader />
      <main>
        <Highlights />
        <Ecosystem />
      </main>
    </Layout>
  );
}
