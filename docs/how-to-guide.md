# How to Use Each Prompt

A plain-English guide to every step in the Civic Transparency Toolkit. You don't need to understand any of the technical details to use these — the app runs them for you. This guide is here so you know what each step does and what to expect.

---

## Prompt 1: News Aggregator

**What it does:** Scans all the websites you've set up (city council agendas, school district sites, local news, etc.) and finds 15-25 things that might be stories worth telling your community about.

**Think of it as:** A really thorough neighbor who reads every city council agenda, every school board announcement, and every local news article — then tells you the 20 most interesting things they found.

**What you'll see in the output:**
- A list of story leads organized by topic (Government, Education, Infrastructure, etc.)
- For each lead: a short summary, why it matters, who to contact for more information, and a confidence score (how likely this is a real story)
- A calendar of upcoming public meetings and deadlines

**Tips:**
- Leads with a confidence score above 0.70 are the strongest ones
- The more source URLs you give the toolkit, the better this step works
- If you have a YouTube channel for your city council meetings, the toolkit can pull transcripts from those too

**When to use it:** This runs automatically as the first step of Daily Production. You probably won't need to run it by itself unless you're experimenting.

---

## Prompt 2: Story Expansion

**What it does:** Takes the best leads from Prompt 1 and turns each one into a full story with context, background, specific facts, and proper sourcing.

**Think of it as:** Taking a sticky note that says "City council voted on a new water rate" and turning it into a complete article that explains what the new rates are, why they changed, who voted how, and what it means for your water bill.

**What you'll see in the output:**
- 5-10 expanded stories, each 400-800 words
- Clear headlines
- Dollar amounts, dates, names, and vote counts where applicable
- A source transparency section showing where each fact came from
- A list of leads that weren't expanded and why

**Tips:**
- Stories sourced from local news articles are fine — the toolkit credits the original outlet
- If a story seems thin, it might be because the original source didn't have much detail
- You can run this step again with different leads if you want to try different stories

**When to use it:** Runs automatically as the second step of Daily Production.

---

## Prompt 3: Black Desk (Speculative Radar)

**What it does:** Looks for patterns and whispers that might be worth investigating — things that aren't confirmed but feel like something is going on. Reads community chatter (Reddit, Nextdoor, Facebook) alongside official records and asks: "Is there something real here?"

**Think of it as:** That neighbor who says "I've been hearing a lot of people complain about water pressure on the south side of town, and I noticed the city just quietly approved a new industrial hookup over there..." It's connecting dots that might mean something.

**What you'll see in the output:**
- A list of speculative signals (not confirmed stories — hunches backed by patterns)
- Each signal has a strength score (how many dots connect) and a confidence score (always low, by design — these are leads, not facts)
- Recommendations: investigate further, watch for more evidence, or discard

**Important:** This prompt does NOT produce publishable stories. It produces questions worth asking. Never share Black Desk output as fact.

**When to use it:** Runs as part of the Signal Intelligence pipeline. Use this when you want to dig deeper than daily news — looking for things the official channels aren't talking about.

---

## Prompt 4: Dark Signal Desk (Verification)

**What it does:** Takes the hunches from the Black Desk and tries to either confirm or kill them. Forces the system to look for counter-evidence and opposing viewpoints before anything moves forward.

**Think of it as:** A skeptical friend who says "Okay, you think there's a pattern with the water pressure — but did you check if there's a maintenance schedule? Did you call the water department? Is anyone actually saying this is a problem, or is it just two Reddit posts?"

**What you'll see in the output:**
- Each signal gets run through four verification gates
- Signals that survive get a confidence score and a handoff recommendation (who to contact, what records to request)
- Signals that fail get documented with a reason why

**Tips:**
- If a signal is marked "FOR VERIFICATION," it means there's enough evidence to pursue it as a real story
- The handoff will tell you exactly what official record you'd need to confirm the story
- Most signals from the Black Desk will NOT survive this step, and that's by design

**When to use it:** Runs automatically as the second step of Signal Intelligence.

---

## Prompt 5: Integrity Checker

**What it does:** Reads through finished stories and checks them for accuracy. Verifies facts, checks that sources are properly credited, and flags anything that looks wrong.

**Think of it as:** A careful proofreader who asks "Wait, you said the vote was 5-2, but did you check that?" and "You mentioned a $3 million budget, but your source says $3.2 million."

**What you'll see in the output:**
- For each story: READY (good to go), CORRECTIONS NEEDED (fix these specific things), or HOLD (something is wrong enough that you should verify before sharing)
- Specific flags for claims, links, dollar amounts, dates, and quotes
- Suggestions for missing context (things the story should mention but doesn't)

**Tips:**
- A "HOLD" doesn't mean the story is bad — it means you should double-check something before sharing it
- "UNVERIFIED" is different from "WRONG" — it means the checker couldn't independently confirm a claim, not that the claim is false
- Stories sourced from local news will NOT be flagged just for using journalism as a source

**When to use it:** Runs automatically as part of Daily Production (between Story Expansion and the final rewrite). You can also run it by itself in Single Prompt mode on any story you want to fact-check.

---

## Prompt 6: First Amendment Counsel

**What it does:** Explains your legal rights when someone tries to stop you from accessing public information or sharing civic news. Covers public records requests, meeting access, publishing rights, and how to respond to legal threats.

**Think of it as:** Having a knowledgeable friend who used to work at a newspaper and knows the basics of press freedom law — NOT a substitute for an actual lawyer, but someone who can tell you "You have the right to attend that meeting" or "That cease-and-desist letter doesn't actually mean what they're claiming."

**What you'll see in the output:**
- If you describe a threat or access denial: a severity rating, immediate actions to take, and relevant legal principles
- If you ask a question: a clear explanation with references to actual laws and court cases

**Important:** This is NOT legal advice. If you receive a real legal threat, consult an actual attorney. This prompt gives you a starting point for understanding your rights, not a legal defense.

**When to use it:** Run it in Single Prompt mode whenever you need guidance on a legal question related to civic transparency, public records, or publishing rights.

---

## Prompt 7: Community News Writer

**What it does:** Takes the expanded, fact-checked stories and rewrites them as clean, readable articles that anyone can understand. This is the final output — the stories you actually share with people.

**Think of it as:** A friendly neighbor who happens to be a good writer, taking a government document full of jargon and turning it into "Here's what the city council just did and why you should care."

**What you'll see in the output:**
- 400-800 word stories written in plain, conversational English
- Each story has a clear headline, full paragraphs (no bullet points), a "Why This Matters" section, a "What's Next" section, and source credits
- Government jargon is explained on first use ("ordinance" becomes "an ordinance — a required step in passing a new city law")

**Tips:**
- These stories are designed to be copy-pasted directly into newsletters, emails, or social media posts
- The "What's Next" section is especially useful — it tells you about upcoming votes, deadlines, or meetings where you can get involved
- If a story seems too short, it's because the source material was limited, not because the toolkit cut information

**When to use it:** Runs automatically as the final step of Daily Production. This is where you get your community-ready stories.

---

## Prompt 8: Source Integrity Protocol

**What it does:** Makes sure the toolkit writes original content instead of copying from other people's articles. It's the system's plagiarism prevention layer.

**Think of it as:** The voice in the back of your head that says "Write this in your own words — don't just rearrange what the newspaper said."

**What it enforces:**
- Every sentence must be original (the toolkit's own writing, not rephrased from a source)
- Every fact must be attributed (readers should know where information came from)
- Local journalism gets credit when it's the reason the toolkit knows about a story
- No story is suppressed just because it was first reported by a newspaper — but the toolkit can't copy the newspaper's article

**When to use it:** You probably won't ever run this directly. It operates as a set of rules that the other prompts follow. It's included here so you know it exists and what it does.

---

## Prompt 9: Story Research & Writing

**What it does:** A standalone research and writing tool. You give it a topic ("What's happening with the new housing development on Main Street?") and it does its own research, verifies what it finds, and writes a complete story.

**Think of it as:** Asking a really capable research assistant to "look into this for me and write it up." They'll check multiple sources, find competing viewpoints, note what they couldn't verify, and give you a finished article.

**What you'll see in the output:**
- A complete story (400-1,200 words depending on complexity)
- Source documentation showing where every fact came from
- Verification notes flagging any claims the system couldn't independently confirm
- Gaps — things the story should address but the system couldn't find information about

**Tips:**
- Be specific with your topic. "What's happening with housing?" will give you less than "What's happening with the 900-unit development proposed for Highway 119 and Hover Street?"
- The system has three modes: QUICK-TURN (short, fast), STANDARD (full story), and DEEP INVESTIGATION (thorough, longer). The app defaults to STANDARD.
- This prompt works best when you already have a specific question you want answered

**When to use it:** Select "Ad-Hoc Story" from the pipeline dropdown, type your topic in the input area, and press "Run Complete."

---

## Quick Reference: Which Prompts Run When?

| Pipeline Lane | Steps That Run | What You Get |
|--------------|----------------|--------------|
| **Daily Production** | 1 → 2 → 5 → 7 | Community-ready stories from today's sources |
| **Signal Intelligence** | 3 → 4 | Investigative leads worth pursuing |
| **Ad-Hoc Story** | 9 | One researched story on your topic |
| **Single Prompt** | Any one you pick | Run any step individually |

---

## Still Have Questions?

The prompts themselves are plain text files in the `prompts/` folder. You can open them in any text editor (Notepad, TextEdit, VS Code) to read the full instructions the AI follows. They're written to be readable, not just by the AI, but by you.

If something isn't working the way you expect, check the output from the step before the one that's giving you trouble. The pipeline is a chain — if Step 1 didn't find good leads, Step 2 won't have much to work with.
