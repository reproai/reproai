# Submissions

This folder is the demo-phase intake for reproducibility-certificate
submissions. Because reproai.org has no upload server yet, an author submits by
opening a **pull request** that adds one archive here; CI verifies it as
untrusted data (it never runs the author's code), and a maintainer reviews,
signs, and publishes it to [reproai.org/certs](https://reproai.org/certs).

## How a submission flows

1. **Author** runs `reproai certify` then `reproai submit --export`, producing a
   single `<cert-id>.zip`.
2. **Author** opens a PR adding that zip under `submissions/<cert-id>.zip`
   (`reproai submit --pr` drafts this for you), or emails it to
   `certs@reproai.org` if they have no GitHub account.
3. **CI** (`.github/workflows/verify-submission.yml`) runs
   `reproai verify-submission` on the archive: it screens the zip
   (decompression-bomb, size, file-count, path-traversal), checks the bundle
   shape, and runs offline provenance verification. **No author code is ever
   executed.**
4. **Maintainer** reviews (see [`core/MAINTAINER_RUNBOOK.md`](../core/MAINTAINER_RUNBOOK.md)),
   signs the certificate as the registry, deposits it into the live site, and
   merges. Merge + publish is the "witness" step.

A submission is a *request*; publication happens on acceptance. Merged archives
may be pruned once published — the published certificate lives in the site
registry, and its trust lives in the certificate itself, not in this folder.

## What a submission archive contains

The certificate and its trace, the output blobs, the closed package copy, a
`results/` view, the badge/seal, author-confirmed `submission_metadata.json`,
and a `SUBMISSION.md` cover note. See `reproai submit --help`.

## Scope

A certificate attests that the listed output files were produced by this code
and data, in this environment, in a run bound to a public timestamp. It does not
judge whether the paper's conclusions are correct — reproducible is not the same
as correct.
