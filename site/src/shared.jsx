/*
 * shared.jsx — chrome reused across every page (landing + changelog).
 *
 * Nav and Footer read their labels from content.js, so copy still lives in one place.
 * `withCode` turns `backtick` spans in plain prose into <code> — used by both pages.
 *
 * Nav takes a `home` prop:
 *   home={true}  (landing page)  → section links are in-page anchors (#install) that smooth-scroll
 *   home={false} (other pages)   → the same links point back to the landing page (/#install)
 */
import React from "react";
import { content } from "./content.js";

// render `inline code` from backticks and ==highlight== from double-equals, in a plain content string
export function withCode(text) {
  const nodes = [];
  text.split("`").forEach((seg, i) => {
    if (i % 2 === 1) {
      nodes.push(<code key={`c${i}`}>{seg}</code>);
    } else {
      seg.split("==").forEach((part, j) => {
        if (j % 2 === 1) nodes.push(<span className="hl" key={`h${i}-${j}`}>{part}</span>);
        else if (part) nodes.push(<React.Fragment key={`t${i}-${j}`}>{part}</React.Fragment>);
      });
    }
  });
  return nodes;
}

export function Nav({ home = true }) {
  // on non-home pages, section anchors resolve against the landing page
  const prefix = home ? "" : "/";
  return (
    <nav className="nav">
      <a className="brand" href={home ? "#top" : "/"}>
        <span className="brand-mark">{content.brand.mark}</span>
        <span className="brand-name">{content.brand.name}</span>
      </a>
      <div className="nav-links">
        {content.nav.links.map((l) => (
          <a key={l} href={`${prefix}#${l.toLowerCase()}`}>{l}</a>
        ))}
        <a className={`nav-changelog${home ? "" : " current"}`} href="/changelog/">
          Changelog
        </a>
      </div>
    </nav>
  );
}

export function Footer() {
  return (
    <footer className="footer">
      <div className="footer-inner">
        <div className="brand">
          <span className="brand-mark">{content.brand.mark}</span>
          <span className="brand-name">{content.brand.name}</span>
        </div>
        <div className="footer-links">
          {content.footer.links.map((l) => (
            <a key={l.label} href={l.href} {...(l.newTab ? { target: "_blank", rel: "noopener noreferrer" } : {})}>{l.label}</a>
          ))}
        </div>
        <div className="footer-note">{content.footer.note}</div>
      </div>
    </footer>
  );
}
