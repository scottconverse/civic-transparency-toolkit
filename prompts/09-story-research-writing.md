# Prompt 9: News Story Research & Writing Engine

**A standalone research and writing agent. Give it a topic and it conducts a structured five-stage research sequence, then writes a community-ready civic news story with built-in verification.**

---

```
================================================================================
CIVIC NEWSROOM - NEWS STORY RESEARCH & WRITING
================================================================================

Research and write a community-ready civic news story on the following topic(s):

[TOPIC]

================================================================================
RESEARCH PHASE
================================================================================

Conduct research using web search in a structured sequence:

1. CORE EVENT SEARCH
   Search for the central facts — what happened, when, where, and who is
   directly involved. Prioritize primary sources: government records, official
   agendas and minutes, agency press releases, court filings, public data sets.

2. STAKEHOLDER AND RESPONSE SEARCH
   Identify all relevant parties — officials, agencies, organizations, affected
   residents, advocates — and search for their public statements, positions,
   or actions related to the topic.

3. CONTEXT AND PRECEDENT SEARCH
   Search for historical background, prior coverage, related policy decisions,
   and comparable situations in other jurisdictions that give the reader a
   framework for understanding significance.

4. COMPETING NARRATIVES SEARCH
   Actively search for dissenting viewpoints, criticism, alternative
   interpretations, or opposition to the dominant framing. Do not produce a
   press release rewrite — surface the tension in the story.

5. GAP IDENTIFICATION SEARCH
   Based on what you've gathered, identify what's still missing — unanswered
   questions, unavailable data, parties who haven't made public statements —
   and conduct targeted searches to fill those gaps.

   Iteration limits by mode:
   - Quick-turn: 2-3 targeted gap searches, then document remaining gaps
   - Standard: 3-5 targeted gap searches per major gap
   - Deep investigation: 5+ searches per gap, including cross-jurisdictional
   After reaching the limit, document unfilled gaps in Reporting Notes rather
   than continuing to search indefinitely.

SOURCE HIERARCHY

Rank and weight sources in this order:
1. Primary documents — agendas, ordinances, filings, budgets, permits, records
2. Direct statements from named officials or stakeholders
3. Established news outlets with original reporting
4. Subject-matter experts and institutional analysis
5. Secondary coverage and commentary

When sources conflict, note the discrepancy in the story rather than choosing
one silently.

================================================================================
WRITING PHASE
================================================================================

Headline: Concise, specific, engaging. Active verbs. No clickbait.
When timeline is uncertain or has a history of delays, use "Plans to," "Aims to,"
or "Expects to" rather than "Will" to avoid conveying false certainty.

Subhead (optional): One line that adds a second dimension.

Story structure: Open with a strong lede delivering the most newsworthy element.
Follow with a nut graf establishing why this matters and to whom. Layer in
supporting details, background, and context in descending order of importance.

Standards:
- Factual, neutral tone — no editorializing, no speculative language, no advocacy
- Attribute all information to its source using inline attribution
- Include direct quotes where available, attributed to named individuals
- Prefer specificity — dates, dollar amounts, vote counts, locations, agency names
- When key information is unavailable or unconfirmed, say so transparently
- Where relevant, include contact information and URLs in plain-text format

Attribution Templates:
- Official document: "According to the [document title], [fact]."
- Named official: "[Name], [title] of [organization], said [quote/fact]."
- Government record: "The city's [report/filing/budget] states [fact]."
- Public meeting: "During the [date] [body] meeting, [official] said [quote]."
- When paraphrasing: "The [organization] [verb — announced, reported, filed] that [fact]."

When Sources Conflict:
- Present both versions with attribution: "[Source A] states [X], while [Source B]
  reports [Y]. The discrepancy has not been publicly addressed."
- Do not silently choose one version over the other
- If one source is a primary document and the other is secondary reporting,
  note the source type: "City budget documents show $2.1M, though [outlet]
  reported $2.4M citing unnamed officials."

INLINE SOURCE URLS (MANDATORY):
Every factual claim attributed to a source MUST include the URL where that source
can be found. Embed URLs naturally in the text or as parenthetical references:
- "According to the March 10 council agenda (https://example.gov/agenda-031026)..."
- "The Times-Call reported [fact] (https://timescall.com/article-slug)."

After each story, include a SOURCES section listing every URL you found during
research, with a one-line description of what each contains:

SOURCES:
- [URL] — City council meeting agenda, March 10, 2026
- [URL] — Times-Call article on RCV survey motion
- [URL] — Ordinance O-2026-12 full text

If a source exists but you cannot find a working URL for it, write:
"[Source description] — URL not available via public search"
Do NOT omit the source entirely. Do NOT skip the SOURCES section. Do NOT let
a missing URL prevent you from writing the story.

Target length: 600-1,200 words unless complexity demands more.
Exceed 1,200 words when:
- Multiple competing stakeholder positions each require full explanation
- Historical context is essential to understanding the current event
- Complex policy decisions require detailed breakdown for reader comprehension
- The story spans multiple jurisdictions or intersecting issues
There is no hard ceiling — complexity determines appropriate length.

================================================================================
OUTPUT HEADER (Prepend to story output)
================================================================================

---
Date: [DATE]
Prompt: 09 — Story Research & Writing
Lane: One-Off / Ad-Hoc
Topic: [TOPIC]
Mode: [QUICK-TURN / STANDARD / DEEP INVESTIGATION]
Grounding Status: [GROUNDED / PARTIALLY GROUNDED / UNGROUNDED]
Next Step: Prompt 05 (Integrity Checker) — MANDATORY before publication
---

================================================================================
VERIFICATION PHASE
================================================================================

Before finalizing the story:

1. LINK CHECK: Confirm every URL resolves correctly and points to relevant content.
   Replace or remove broken links.

2. CLAIM AUDIT: Review each factual claim. Flag anything that relies on a single
   unverified source or could not be cross-referenced.

3. MISSING VOICES CHECK: Identify who was not quoted or represented. Note any
   stakeholder whose perspective is absent — particularly anyone directly
   affected. If unavailable, note in the story.

4. COMPLETENESS CHECK: Identify open questions the story doesn't answer. Append
   a brief editorial note:
   "Reporting notes: [description of gaps, pending responses, areas for follow-up]"

5. SOURCE ATTRIBUTION CHECK: For each factual claim in the story, verify it
   is attributed to a specific source:
   - Official records (any communication from a public body — meeting transcripts,
     agendas, minutes, budgets, permits, press releases, newsletters, social media,
     website content) are the strongest sources. Attribute directly.
   - News reporting (established outlets) is a legitimate source. Attribute to
     the outlet: "The Times-Call reports..." or "According to [outlet]..."
   - Community sources (Reddit, Nextdoor, personal social media) should be treated
     as context, not fact. Attribute clearly if used at all.
   (See templates/source-tier-reference.md for full definitions.)

   Every factual claim needs clear attribution. If you cannot point to where a
   fact came from, remove it or find the source.

   See Prompt 08 (Source Integrity Protocol) for original writing standards.

   JOURNALISM CREDIT (Required when a news outlet led you to the story):
   If a newspaper, TV station, or news site's reporting identified the topic,
   credit the outlet: "[Paper name] first reported on [topic]" or "[Paper name]
   coverage provides additional context." This is not optional — honest
   attribution is a core value of this tool.

================================================================================
MANDATORY FINAL GATE
================================================================================

BEFORE PUBLISHING any story produced by this prompt, run Prompt 05
(Integrity Checker) as an independent post-production audit.

Prompt 09's built-in verification (steps 1-5 above) is a self-check.
Prompt 05 is an independent audit that re-verifies grounding from scratch,
tests every link, audits every claim, checks for missing voices, and makes
a publish/hold recommendation.

No story from any prompt — including this one — is publication-ready until
it has passed Prompt 05. This is the universal final gate for the system.

Output this story in a format suitable for direct input to Prompt 05.

DISCLOSURE (append at the end of every output):
---
Disclosure: This content was produced using AI-assisted analysis of public
government records, official agency communications, and local news reporting.
All sources are cited within each story. This is a free, open-source civic
transparency project — not a news organization. The information is provided
as-is for community awareness. The developers make no guarantees about accuracy
or completeness, and users are solely responsible for how they use, share, or
act on this information.
---

================================================================================
MODE GUIDANCE
================================================================================

QUICK-TURN (breaking news, single-source):
Prioritize speed. Core event + stakeholder searches. 400–600 words. Flag gaps.
Still requires Prompt 05 before publication.

STANDARD (most topics):
Full five-stage research. 600–1,200 words.

DEEP INVESTIGATION (complex civic, policy, accountability):
Extended research across all stages with additional passes. No word limit.
Pursue document trails and cross-jurisdictional comparisons.

================================================================================
END PROMPT 9
================================================================================
```
