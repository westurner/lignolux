---
name: chat-research-brief
description: 'Turn chat-search evidence into a one-page research brief with traceable citations. Use after /search-chats results.'
argument-hint: 'Topic or question for the brief'
---
Create a concise one-page research brief from chat evidence.

## Inputs
- Main question or topic: {{input}}
- Search evidence from `/search-chats` or `/search-chats-sources`

## Output Requirements
1. Use sections:
- Question
- Key Findings
- Evidence Table
- Conflicts and Uncertainty
- Practical Implications
- Next Queries

2. Evidence Table must include:
- Claim
- Source file
- Line(s)
- Confidence (High/Medium/Low)

3. Citation rules:
- Every claim must map to at least one file+line citation.
- If evidence is weak or contradictory, label it explicitly.

4. Style:
- Maximum ~500 words for narrative body.
- Prefer specific, testable statements over broad summaries.
