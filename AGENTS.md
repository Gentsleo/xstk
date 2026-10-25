# Session Continuity & Context Hygiene Rules

## 1. Automated Session Continuity (Resume from Handoff)
At the start of every session or when resuming work in this workspace:
- Check if `.handoff.md` or `.compact_context.md` exists in the project root.
- If present, immediately inspect and ingest the document:
  - **Verified Knowledge**: Treat platform specs, architectural invariants, and key file anchors as established ground truth. Do not re-scan or re-verify what is already proven.
  - **Root Cause Analysis**: Adopt the verified failure mechanism and proof without re-running exploratory diagnostic steps.
  - **Work Completed vs Pending**: Pick up directly from the earliest pending task.
  - **Exact Code Modifications**: Apply or verify the intended surgical changes.
- Seamlessly continue execution without asking the user for background already recorded in the handoff.

## 2. Context Window & Compaction Discipline
- The active context window limit is strictly bounded to 400K tokens.
- At 60% context threshold (~240K tokens), compaction / handoff triggers.
- In-flight context hygiene:
  - Keep tool outputs concise; rely on artifacts for outputs exceeding 50 lines.
  - Avoid redundant file reads (`compaction.supersedeReads` is active).
  - Prioritize structured technical facts over narrative summaries.
