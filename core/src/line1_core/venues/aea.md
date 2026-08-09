# AEA venue profile — notes & sources

Human-readable companion to `aea.yaml`. American Economic Association journals
(AER, the AEJ family, JEL, JEP). Profile version 2026-06-15.

> Digest fetched from official sources on 2026-06-15. Anything not verifiable from an
> official source is marked NOT FOUND rather than guessed.

## Deposit

- **Repository:** AEA Data and Code Repository on openICPSR.
- **DOI:** `10.3886/E{project-number}V1` (version suffix increments).
- **Unzipped:** deposit unzipped unless more than 1,000 files.
- **Size:** request a quota increase above 30 GB.

## README

- Must be `README.pdf` in the **uppermost** directory, PDF format.
- SSDE Template README v1.1 strongly encouraged (DOI 10.5281/zenodo.7293838).
- Required content: data availability & provenance statement; rights statement; each
  data source; dataset list; computational requirements (software/versions, memory,
  runtime, storage); program/code description; **program-to-output map** (programs →
  tables, figures, in-text numbers); instructions to replicators; references.

## Environment

- Must state software names+versions, package names+versions, hardware, memory, disk,
  expected wall-clock time. Setup program encouraged; master script strongly encouraged.

## Reproduce scope & tolerance

- Must reproduce **all tables, all figures, and all non-trivial in-text numbers**.
- **No manual intervention** except a single change to set program/data directory paths.

## Confidential / restricted data

- State reasons in the data availability statement; provide private access to the Data
  Editor and/or a third-party replicator; do not upload non-public data to the public draft.
- Dual package (public + confidential). A synthetic/fake dataset is recommended for a
  functionality test.

## License

- openICPSR default CC-BY-4.0. Archive-agreement preference: data CC-BY, code Modified BSD.

## Required forms

- Data and Code Information Form; Data and Code Availability Form; Data and Code Archive Agreement Form.

## Sources

- https://www.aeaweb.org/journals/data
- https://www.aeaweb.org/journals/data/data-code-policy
- https://www.aeaweb.org/journals/data/data-legality-policy
- https://aeadataeditor.github.io/aea-de-guidance/
- https://aeadataeditor.github.io/aea-de-guidance/preparing-for-data-deposit.html
- https://aeadataeditor.github.io/aea-de-guidance/data-deposit-aea.html
- https://zenodo.org/records/7293838
- https://www.aeaweb.org/journals/forms/data-code-availability
