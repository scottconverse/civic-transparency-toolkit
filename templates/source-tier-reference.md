# Source Reference Guide

**Version:** 4.0
**Last Modified:** March 13, 2026

**Shared reference for all Civic Transparency Toolkit prompts. This document defines the source categories used throughout the toolkit and how each should be handled.**

---

## This Is a Community Tool

The Civic Transparency Toolkit is not a newspaper. It is a tool that helps
residents stay informed about what is happening in their city. The people
who use it will paste stories into newsletters, email them to council
members, share them on Facebook, and use them to prepare CORA requests.

The source system exists for TRANSPARENCY — so readers know where information
comes from. It is not a kill switch. Accurate, attributed information from
any legitimate source should reach residents.

---

## Official Records

**ANY communication from a public governing body or public agency that the
body produced and published.**

What qualifies (ALL formats):

- Meeting transcripts (auto-generated or official)
- Meeting agendas, packets, and minutes
- Audio/video recordings of public meetings
- Resolutions, ordinances, and municipal code
- Approved budgets and budget amendments
- Building permits, zoning applications, and land use filings
- Signed contracts, procurement awards, and RFP documents
- Audit reports
- Court filings and public judicial records
- Official press releases
- Official newsletters
- Official social media posts (from verified accounts)
- Official website content
- Public data portals (.gov, .edu domains)

Which public bodies count:

- City council and city departments
- School districts and school boards
- County commissions and county departments
- Transit authorities (RTD, etc.) and their boards
- Planning commissions
- State agencies and departments
- Special districts (fire, water, library, etc.)
- Any other public governing body created by law

**How to use:** Attribute directly. "According to the March 10 meeting
transcript..." or "Per the SVVSD website..." These are the strongest
sources and need no additional caveats.

---

## News Reporting

**Established news outlets with original reporting.**

What qualifies:

- Local newspapers (e.g., Times-Call, Daily Camera)
- Television news stations
- News websites and online-only outlets
- Wire services (AP, Reuters)
- Regional and national outlets covering local stories
- Independent journalism outlets (e.g., Boulder Reporting Lab)

What does NOT qualify as news reporting (these are official records):

- A school district's own website, newsletter, or social media
- A transit agency's official service announcements
- A county commission's published meeting materials
- Any communication produced by the government body itself

**How to use:** Attribute to the outlet. "The Times-Call reports that..."
or "According to Denverite..." News reporting is a legitimate source of
accurate civic information. When it leads you to a story, credit the outlet.

News reporting is NOT a lesser source that must be independently verified
before publishing. It IS a source that must be attributed honestly.

---

## Community Sources

**Social media, forums, personal accounts, and other informal channels.**

What qualifies:

- Reddit community posts and threads
- Nextdoor neighborhood discussions
- Facebook community group posts
- YouTube comments
- Personal blogs and opinion pieces
- Unverified personal social media posts
- Anonymous tips or complaints

**How to use:** Treat as signals, not facts. These can tell you what
residents are discussing or concerned about, but individual claims should
be treated with skepticism. Do not build stories solely on community
sources unless the community discussion itself is the story (e.g.,
"Residents on Nextdoor are organizing against a proposed development").

---

## How Sources Flow Through the Pipeline

```
News Aggregator (Prompt 01)   -> Finds leads from all source types
Story Expansion (Prompt 02)   -> Writes stories using official records AND
                                 news reporting; attributes all sources
Integrity Checker (Prompt 05) -> Checks factual accuracy and attribution
Community Writer (Prompt 07)  -> Rewrites stories in plain language for
                                 residents; preserves attribution
```

The Black Desk (Prompt 03) and Dark Signal Desk (Prompt 04) use community
sources as starting points, then verify through official records and news
reporting.

The Source Integrity Protocol (Prompt 08) ensures original writing with
honest attribution. It prevents copying — not sourcing.
