import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { content, GH } from "./content.js";
import { Nav, Footer, withCode } from "./shared.jsx";

function EnginePanel() {
  const stages = content.engine.stages;
  const [active, setActive] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setActive((a) => (a + 1) % stages.length), 1100);
    return () => clearInterval(id);
  }, [stages.length]);

  const container = {
    hidden: { opacity: 0, y: 24 },
    show: { opacity: 1, y: 0, transition: { duration: 0.6, ease: "easeOut", staggerChildren: 0.08, delayChildren: 0.15 } },
  };
  const item = { hidden: { opacity: 0, y: 10 }, show: { opacity: 1, y: 0, transition: { duration: 0.4 } } };

  return (
    <motion.div
      className="engine"
      variants={container}
      initial="hidden"
      whileInView="show"
      viewport={{ once: true, amount: 0.3 }}
    >
      <span className="glow glow-a" aria-hidden="true" />
      <span className="glow glow-b" aria-hidden="true" />

      <div className="engine-head">
        <div className="lights"><i className="l r" /><i className="l y" /><i className="l g" /></div>
        <span className="engine-title">{content.engine.title}</span>
      </div>

      <motion.div className="engine-body" variants={container}>
        <motion.div className="engine-block input" variants={item}>
          <div className="block-label">{content.engine.inputLabel}</div>
          <div className="block-text">{content.engine.inputText}</div>
        </motion.div>

        <motion.div className="engine-stages" variants={item}>
          {stages.map((s, i) => (
            <div className={`stage ${active === i ? "on" : ""}`} key={s.name}>
              <span className="stage-tick" />
              <div className="stage-text">
                <div className="stage-name">
                  <code className="stage-cmd">{s.name}</code>
                  {s.runs && <span className="stage-tag">{content.engine.runsTag}</span>}
                </div>
                <div className="stage-note">{s.note}</div>
              </div>
              <span className="stage-run" aria-hidden={active !== i}>{content.engine.working}</span>
            </div>
          ))}
        </motion.div>

        <motion.div className="engine-block output" variants={item}>
          <div className="block-label">{content.engine.outputLabel}</div>
          <ul className="advisory">
            {content.engine.advisory.map((a) => (
              <li key={a.label}><span className={`pill ${a.cls}`}>{a.label}</span> {a.text}</li>
            ))}
          </ul>
          {content.engine.advisoryNote && (
            <p className="advisory-note">{content.engine.advisoryNote}</p>
          )}
        </motion.div>

        <motion.div className="engine-evolve" variants={item}>
          <span className="evolve-dot" aria-hidden="true" />
          <div className="evolve-text">
            <code className="stage-cmd">{content.engine.map.cmd}</code>
            <span className="evolve-note">{content.engine.map.note}</span>
          </div>
        </motion.div>

        <motion.div className="engine-evolve" variants={item}>
          <span className="evolve-dot" aria-hidden="true" />
          <div className="evolve-text">
            <code className="stage-cmd">{content.engine.update.cmd}</code>
            <span className="evolve-note">{content.engine.update.note}</span>
          </div>
        </motion.div>
      </motion.div>
    </motion.div>
  );
}

function Hero() {
  const h = content.hero;
  return (
    <header id="overview" className="hero section">
      <div className="hero-left">
        <div className="eyebrow">{h.eyebrow}</div>
        <h1>
          {h.headline.lead}<br />{h.headline.rest}<span className="red">{h.headline.emph}</span>{h.headline.tail}
        </h1>
        <p className="lede">{withCode(h.lede)}</p>
        <div className="cta">
          <a className="btn primary" href={GH}>{h.ctaPrimary}</a>
          <a className="btn ghost" href="#install">{h.ctaGhost}</a>
        </div>
        <div className="hero-meta">
          <span className="dot" /> {h.meta}
        </div>
      </div>
      <div className="hero-right">
        <EnginePanel />
      </div>
    </header>
  );
}

function Term({ lines }) {
  return (
    <div className="term">
      {lines.map((line, i) => (
        <div className="term-line" key={i}>
          {line.length === 0 ? "\u00a0" : line.map((tok, j) => (
            <span key={j} className={`tk ${tok.c || ""}`}>{tok.t}</span>
          ))}
        </div>
      ))}
    </div>
  );
}

function Bib({ lines }) {
  return (
    <div className="term">
      {lines.map((line, i) => (
        <div className="term-line" key={i}>
          {line.length === 0 ? "\u00a0" : line.map((tok, j) => (
            <span key={j} className={`tk ${tok.c || ""}`}>{tok.t}</span>
          ))}
        </div>
      ))}
    </div>
  );
}

function AiInstall({ ai }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard?.writeText(ai.prompt).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  };
  return (
    <div className="card ai-install">
      <span className="redline" />
      <h3>{ai.title}</h3>
      <div className="term ai-prompt">
        <div className="cite-label-row">
          <div className="cite-label">{content.install.aiLabel}</div>
          <button className="copy" onClick={copy}>{copied ? content.cite.copyDone : content.cite.copyIdle}</button>
        </div>
        <div className="term-line ai-prompt-text">{ai.prompt}</div>
      </div>
      <p className="term-note">{withCode(ai.note)}</p>
    </div>
  );
}

function Install() {
  const c = content.install;
  return (
    <section id="install" className="section">
      <SectionHead lead={c.head.lead} emphasis={c.head.emphasis} sub={c.head.sub} />
      <div className="cards ai-install-row">
        <AiInstall ai={c.ai} />
      </div>
    </section>
  );
}

function Usage() {
  const c = content.usage;
  return (
    <section id="usage" className="section">
      <SectionHead lead={c.head.lead} emphasis={c.head.emphasis} sub={c.head.sub} />
      <div className="cards two">
        <div className="card">
          <span className="redline" />
          <h3>{c.cli.title}</h3>
          <Term lines={c.cli.runLines} />
          <ul className="term-notes">
            {c.cli.notes.map((n, i) => <li key={i}>{withCode(n)}</li>)}
          </ul>
        </div>
        <div className="card">
          <span className="redline" />
          <h3>{c.app.title}</h3>
          <p>{withCode(c.app.intro)}</p>
          <div className="chat">
            <div className="chat-head"><span className="chat-dot" />{c.app.speaker}</div>
            <div className="chat-bubble">{c.app.prompt}</div>
          </div>
          <p className="term-note">{withCode(c.app.note)}</p>
        </div>
      </div>
    </section>
  );
}

function SectionHead({ lead, emphasis, sub }) {
  return (
    <div className="section-head">
      <h2>{lead} <span className="red">{emphasis}</span></h2>
      {sub && <p>{withCode(sub)}</p>}
    </div>
  );
}

function Examples() {
  const c = content.examples;
  return (
    <section id="examples" className="section">
      <SectionHead lead={c.head.lead} emphasis={c.head.emphasis} sub={c.head.sub} />
      <div className="cards four">
        {c.items.map((it) => (
          <div className="card" key={it.title}>
            <span className="redline" />
            <h3>{it.title}</h3>
            <ol className="flow">
              {it.flow.map((f, i) => <li key={i}>{withCode(f)}</li>)}
            </ol>
            <div className="card-out">{withCode(it.out)}</div>
          </div>
        ))}
      </div>
    </section>
  );
}

function Contribute() {
  const c = content.contribute;
  return (
    <section id="contribute" className="section">
      <SectionHead lead={c.head.lead} emphasis={c.head.emphasis} sub={c.head.sub} />
      <div className="cards two">
        <div className="card">
          <span className="redline" />
          <h3>{c.cli.title}</h3>
          <Term lines={c.cli.runLines} />
          <ul className="term-notes">
            {c.cli.notes.map((n, i) => <li key={i}>{withCode(n)}</li>)}
          </ul>
        </div>
        <div className="card">
          <span className="redline" />
          <h3>{c.app.title}</h3>
          <p>{withCode(c.app.intro)}</p>
          <div className="chat">
            <div className="chat-head"><span className="chat-dot" />{c.app.speaker}</div>
            <div className="chat-bubble">{c.app.prompt}</div>
          </div>
          <p className="term-note">{withCode(c.app.note)}</p>
        </div>
      </div>
    </section>
  );
}

function FAQ() {
  const c = content.faq;
  const [open, setOpen] = useState(0);
  return (
    <section id="faq" className="section">
      <SectionHead lead={c.head.lead} emphasis={c.head.emphasis} />
      <div className="faq">
        {c.qa.map((item, i) => (
          <div className={`faq-item ${open === i ? "open" : ""}`} key={i}>
            <button className="faq-q" onClick={() => setOpen(open === i ? -1 : i)}>
              <span>{item.q}</span>
              <span className="faq-sign">{open === i ? "−" : "+"}</span>
            </button>
            {open === i && <div className="faq-a">{withCode(item.a)}</div>}
          </div>
        ))}
      </div>
    </section>
  );
}

function Cite() {
  const c = content.cite;
  // the copy-button text is derived from the displayed BibTeX, so the two never drift
  const bib = c.bibLines.map((line) => line.map((tok) => tok.t).join("")).join("\n");
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard?.writeText(bib).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  };
  return (
    <section id="cite" className="section">
      <SectionHead lead={c.head.lead} emphasis={c.head.emphasis} sub={c.head.sub} />
      <div className="cards">
        <div className="card">
          <span className="redline" />
          <div className="cite-label">{c.referenceLabel}</div>
          <h3 className="cite-title">{c.title}</h3>
          <p className="cite-meta">{c.meta}</p>
          <a className="link" href={c.linkUrl}>{c.linkText}</a>
          <div className="cite-bibtex">
            <div className="cite-label-row">
              <div className="cite-label">{c.bibtexLabel}</div>
              <button className="copy" onClick={copy}>{copied ? c.copyDone : c.copyIdle}</button>
            </div>
            <Bib lines={c.bibLines} />
          </div>
        </div>
      </div>
    </section>
  );
}

export default function App() {
  // Arriving from another page via /#section (e.g. the changelog nav) otherwise lands at
  // the top: the section isn't in the DOM until React mounts, so the browser's native
  // anchor scroll — which runs before mount — finds nothing, and its scroll restoration
  // then pins the page at the top. Take over restoration and scroll to the target after
  // mount, re-asserting once more to win against late web-font reflow.
  useEffect(() => {
    const id = window.location.hash.slice(1);
    if (!id) return;
    if ("scrollRestoration" in window.history) window.history.scrollRestoration = "manual";
    const scrollToTarget = () => {
      const el = document.getElementById(decodeURIComponent(id));
      if (el) el.scrollIntoView({ behavior: "instant", block: "start" });
    };
    scrollToTarget();
    const raf = requestAnimationFrame(scrollToTarget);
    const timer = setTimeout(scrollToTarget, 200);
    return () => { cancelAnimationFrame(raf); clearTimeout(timer); };
  }, []);

  return (
    <div id="top">
      <div className="bg-grid" aria-hidden="true" />
      <Nav />
      <Hero />
      <Install />
      <Usage />
      <Examples />
      <Contribute />
      <FAQ />
      <Cite />
      <Footer />
    </div>
  );
}
