import React, { useState, useEffect } from "react";
import { Nav, Footer, withCode } from "./shared.jsx";
import { changelog } from "./changelog-data.js";

// "0.4.0" → "v0.4.0"; a worded label like "Initial release" is shown as-is
const versionLabel = (v) => (/^\d/.test(v) ? `v${v}` : v);

// stable DOM id for a release, used by the floating nav anchors + scroll-spy
const releaseId = (v) =>
  "rel-" + v.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");

const tagClass = { New: "new", Improved: "improved", Fixed: "fixed", Thanks: "thanks" };

function Release({ r }) {
  return (
    <article id={releaseId(r.version)} className="release card">
      <span className="redline" />
      <div className="release-head">
        <h3 className="release-version">{versionLabel(r.version)}</h3>
        <span className="release-date">{r.date}</span>
      </div>
      {r.title && <p className="release-title">{r.title}</p>}
      <ul className="release-changes">
        {r.changes.map((c, i) => (
          <li key={i}>
            <span className={`pill ${tagClass[c.tag] || ""}`}>{c.tag}</span>
            <span className="change-text">{withCode(c.text)}</span>
          </li>
        ))}
      </ul>
    </article>
  );
}

// Floating "Releases" button (bottom-right): appears once you scroll down, opens a
// panel that jumps between versions and highlights the one you're currently reading.
function PageNav({ releases }) {
  const [visible, setVisible] = useState(false);
  const [open, setOpen] = useState(false);
  const [activeId, setActiveId] = useState(null);

  useEffect(() => {
    const onScroll = () => setVisible(window.scrollY > 520);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    const els = releases
      .map((r) => document.getElementById(releaseId(r.version)))
      .filter(Boolean);
    if (!els.length) return;
    const state = {};
    const obs = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          state[e.target.id] = e.isIntersecting;
        });
        const active = els.find((el) => state[el.id]);
        if (active) setActiveId(active.id);
      },
      { rootMargin: "-15% 0px -75% 0px" }
    );
    els.forEach((el) => obs.observe(el));
    return () => obs.disconnect();
  }, [releases]);

  useEffect(() => {
    const onDocClick = (e) => {
      if (!e.target.closest(".pagenav")) setOpen(false);
    };
    document.addEventListener("click", onDocClick);
    return () => document.removeEventListener("click", onDocClick);
  }, []);

  const cls = `pagenav${visible || open ? " visible" : ""}${open ? " open" : ""}`;

  return (
    <div className={cls}>
      <nav className="pagenav-panel" aria-label="Releases">
        <p className="pn-h">Releases</p>
        <ol>
          {releases.map((r) => {
            const id = releaseId(r.version);
            return (
              <li key={id}>
                <a
                  href={`#${id}`}
                  className={activeId === id ? "active" : ""}
                  onClick={() => setOpen(false)}
                >
                  <span className="pn-ver">{versionLabel(r.version)}</span>
                  <span className="pn-date">{r.date}</span>
                </a>
              </li>
            );
          })}
        </ol>
        <a className="pagenav-top" href="#top" onClick={() => setOpen(false)}>
          ↑ Back to top
        </a>
      </nav>
      <button
        type="button"
        className="pagenav-btn"
        aria-expanded={open}
        aria-label="Jump to a release"
        onClick={(e) => {
          e.stopPropagation();
          setOpen((o) => !o);
        }}
      >
        <span className="pagenav-ico" aria-hidden="true">☰</span>
        <span>Releases</span>
      </button>
    </div>
  );
}

export default function Changelog() {
  const c = changelog;
  return (
    <div id="top">
      <div className="bg-grid" aria-hidden="true" />
      <Nav home={false} />
      <main className="section changelog">
        <div className="section-head">
          <h2>{c.head.lead} <span className="red">{c.head.emphasis}</span></h2>
          {c.head.sub && <p>{withCode(c.head.sub)}</p>}
        </div>
        <div className="releases">
          {c.releases.map((r) => (
            <Release key={`${r.version}-${r.date}`} r={r} />
          ))}
        </div>
      </main>
      <Footer />
      <PageNav releases={c.releases} />
    </div>
  );
}
