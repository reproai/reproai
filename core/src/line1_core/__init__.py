"""line1_core — ReproAI Prep pre-diagnose engine. The static commands NEVER execute author code and NEVER issue a reproducibility verdict; they scan a replication package, apply an author rule set and a venue profile, and advise how to reorganize the package so a downstream reproducibility check passes on the first try. The optional debug command runs the package as a smoke test only."""

__version__ = "0.4.10"
GENERATED_BY = f"reproai-prep {__version__}"
