# Civic Transparency Toolkit

A free, open-source desktop app that helps you keep up with what your local government is doing — and turns it into stories you can actually share with your neighbors.

You give it a list of websites to watch (city council agendas, school board sites, local news, etc.), and it reads through them every day, finds the stories that matter to your community, and writes them up in plain English. You can paste those stories into a neighborhood newsletter, email them to your council member, or post them in your local Facebook group.

**This is a community tool, not a newspaper.** It helps regular people stay informed and engaged in civic life.

> **Looking for the prompt-only version?** If you'd rather copy-paste prompts into Claude, ChatGPT, or Gemini without installing anything, see the [Civic Newsroom](https://github.com/scottconverse/civic-newsroom) repo — the same nine-agent pipeline, no coding required.

---

## What You Need Before You Start

**A computer running Windows, Mac, or Linux.** The app runs on your desktop — nothing to install on a server.

**A Claude API key from Anthropic.** This is the AI service that does the reading, analysis, and writing. You get the key from [console.anthropic.com](https://console.anthropic.com). Creating an account is free, but using the API costs a small amount of money each time the toolkit runs.

For a detailed walkthrough of every step in the pipeline, see the [How-To Guide](docs/how-to-guide.md).

**How much does it cost?** A typical daily run costs about **$0.05 to $0.25** (five to twenty-five cents), depending on how many sources you have and which AI model you choose. You can set a monthly spending limit on your Anthropic account so you never get surprised by a bill. At the default settings, running it every day would cost roughly **$5-$10 per month**.

**An internet connection.** The app needs to reach the Claude API and your source websites.

---

## Getting Started (About 5 Minutes)

### Option 1: Download the App (Easiest)

Download the latest release from the [Releases page](https://github.com/scottconverse/civic-transparency-toolkit/releases), unzip it, and double-click `CivicTransparencyToolkit.exe` (Windows) to launch.

### Option 2: Run From the Source Code

If you're comfortable with Python:

```
git clone https://github.com/scottconverse/civic-transparency-toolkit.git
cd civic-transparency-toolkit
pip install -r requirements.txt
python main.py
```

### First-Time Setup

When you open the app for the first time:

1. **Click "Settings"** in the sidebar. Paste in your Claude API key (it starts with `sk-ant-`). The app will explain model choices — Haiku is the default and works great for most people.

2. **Click "City Configuration"** and fill in your city name, state, and open records law (for Colorado, that's CORA). Add your main source URLs here — city website, agenda portal, school district, local newspaper.

3. **Click "Export Template"** to get a starter file you can customize, then **"Import Sources"** to load it back in. This is the easiest way to add a lot of sources at once — you can dump in 5 or 50 URLs and the toolkit will search them all.

4. **Pick "Daily Production"** from the pipeline dropdown and press **"Run Complete"**. The toolkit will search your sources, find stories, fact-check them, and write them up. This takes a few minutes.

---

## How the Pipeline Works

The toolkit runs your sources through a series of steps (called "prompts"). Each step does one job, and the output of one step feeds into the next.

### Daily Production (the main pipeline)

This is what you'll use most of the time. It runs four steps:

**Step 1 → News Aggregator** — Searches all your sources and finds 15-25 things that might be stories. Think of it as a researcher scanning a stack of newspapers and websites and flagging the interesting stuff.

**Step 2 → Story Expansion** — Takes the best leads from Step 1 and expands each one into a full story with context, quotes, and background. Aims for 5-10 publishable stories.

**Step 5 → Integrity Checker** — Reads through the finished stories and flags anything that looks wrong — incorrect facts, missing sources, claims that need verification. Think of it as a fact-checker.

**Step 7 → Community News Writer** — Takes the checked stories and rewrites them as clean, readable articles (400-800 words each) that regular people can understand and share. This is the final output — copy, paste, and go.

### Signal Intelligence (the investigation pipeline)

For digging deeper. Runs two steps:

**Step 3 → Black Desk** — Looks for patterns and whispers that might be worth investigating. It reads community sources (Reddit, Nextdoor, Facebook groups) and asks: "Is there something real behind this noise?"

**Step 4 → Dark Signal Desk** — Takes the Black Desk's hunches and runs them through a structured verification process. If a signal survives all four gates, it gets handed off for reporting.

### Ad-Hoc Story

Runs a single step:

**Step 9 → Story Research & Writing** — You give it a topic ("What's happening with the new development on Main Street?") and it does its own research, then writes a complete story.

### Other Prompts (available in Single Prompt mode)

**Step 6 → First Amendment Counsel** — If you run into a situation where someone tells you that you can't publish something, or denies you access to public records, this prompt explains your rights. It is NOT legal advice — it's a starting point for understanding what the law says.

**Step 8 → Source Integrity Protocol** — Runs automatically behind the scenes. Makes sure the toolkit writes original stories instead of copying from news articles. You probably won't need to run this directly.

---

## Adding Sources

The toolkit watches websites you tell it about. The more sources you give it, the better it works.

### Three Ways to Add Sources

**Just paste URLs** — Open the template file (click "Export Template"), paste URLs one per line, save, and import. The toolkit figures out the rest.

```
https://yourcity.gov/news
https://www.localnewspaper.com/
https://www.schooldistrict.org/category/news/
```

**Label them** — If you want to name your sources:

```
City News: https://yourcity.gov/news
Local Paper: https://www.localnewspaper.com/
School District: https://www.schooldistrict.org/category/news/
```

**Full detail** — If you want to specify the source type and category:

```
City News, https://yourcity.gov/news, Official Record, Government
Local Paper, https://www.localnewspaper.com/, News, Journalism
School District, https://www.schooldistrict.org/category/news/, Official Record, Education
```

An example source list from a real city is included in the repo — see `Real World Example Sources List.csv`.

### Source Types

- **Official Record** — Government websites, council agendas, school district sites, transit agencies. Anything produced by a public body.
- **News** — Newspapers, TV stations, online news outlets. Professional journalism.
- **Community** — Reddit, Nextdoor, Facebook groups, personal blogs. Informal but often where stories start.

Not sure what type to pick? Use "News." The toolkit will search it either way.

---

## Understanding the Output

The final output (from Step 7, the Community News Writer) gives you stories that look like this:

- A **headline** that tells you what happened
- **Story text** in plain paragraphs (no jargon, no bullet points)
- A **"Why This Matters"** section explaining why you should care
- A **"What's Next"** section with dates, meetings, or actions to watch for
- A **"Sources"** section listing where the information came from

Each story is 400-800 words — long enough to be useful, short enough to fit in an email or newsletter.

### What You Can Do With the Stories

- Paste them into a neighborhood newsletter
- Email them to your city council member
- Post them in your local Facebook group or subreddit
- Use them as background when filing a public records request
- Share them with neighbors who don't follow local government

---

## Costs and Models

The toolkit lets you choose which Claude AI model to use. Here's what matters:

| Model | Speed | Cost | Best For |
|-------|-------|------|----------|
| Haiku | Fast | ~$0.03/run | Default — great balance of speed and cost |
| Sonnet | Thorough | ~$0.10/run | When you want deeper analysis |
| Opus | Most capable | ~$0.50/run | When you want the best possible output |

**Tip:** Haiku is the default and handles most civic reporting well. If you want to upgrade specific runs, try Sonnet — it's more thorough but costs more. A full daily run on Haiku costs about $0.03-$0.10.

You can set a monthly spending limit at [console.anthropic.com](https://console.anthropic.com) under Billing. We recommend starting with $10/month to see how it goes.

---

## Frequently Asked Questions

**Is this a newspaper?**
No. It's a community tool. It helps residents stay informed about what their local government is doing. You decide what to do with the information.

**Can I get in legal trouble for sharing these stories?**
The toolkit writes original stories based on public government records and attributed news reporting. It doesn't copy other people's articles. Sharing factual information about public government actions is protected speech.

**How accurate is it?**
The toolkit includes a built-in fact-checker (Step 5) and requires source attribution for every claim. But it's AI-generated content based on public sources — treat it like a well-researched first draft, not gospel. If something seems wrong, check the original source.

**Can I use this for any city?**
Yes. Change the city configuration and source URLs to match your community. The prompts are designed to work for any U.S. municipality.

**What if I don't have many local news sources?**
That's exactly who this tool is for. Even with just a city website and a council agenda portal, the toolkit can find and write up stories. Add community sources (Reddit, Nextdoor) to catch what the official channels miss.

**Does this work on Mac/Linux?**
Yes. Run it from the source code using Python (see "Run From the Source Code" above). You can also build a standalone executable using `build.sh`. The pre-built release is currently Windows only.

**How do I update the prompts?**
The prompts are plain text files in the `prompts/` folder. You can edit them with any text editor. The app reads them fresh each time it runs.

**What's the difference between this and the Civic Newsroom prompt repo?**
[Civic Newsroom](https://github.com/scottconverse/civic-newsroom) is the same nine-agent pipeline as a set of prompts you copy-paste into any LLM — no install, no coding. This toolkit wraps those prompts into a desktop app with a GUI, automated pipeline execution, source management, and DOCX export. Same editorial architecture, different delivery.

---

## Project Structure

```
civic-transparency-toolkit/
├── main.py                              # Launches the app
├── gui.py                               # The desktop interface
├── pipeline.py                          # Runs prompts through the Claude API
├── config.py                            # Saves your settings
├── youtube_transcripts.py               # YouTube transcript fetcher
├── config.json                          # Your settings (auto-created on first run)
├── requirements.txt                     # Python dependencies
├── prompts/                             # The 9 editorial prompts (editable)
├── templates/                           # Source tier reference
├── assets/                              # App icon
├── docs/                                # How-to guide and landing page
├── build.bat                            # Build Windows executable
├── build.sh                             # Build macOS/Linux executable
├── Real World Example Sources List.csv  # Example source list
└── LICENSE                              # MIT License
```

---

## Disclosure

All output is produced using AI-assisted analysis of public government records and attributed news sources. This tool does not replace professional journalism. It helps communities access information that is already public but often hard to find or understand.

Every output from this system must be independently verified by a human before publication. The authors accept no liability for errors in AI-generated output. See the [MIT License](LICENSE) for full terms.

## Credits

Created by **Scott Converse** — see [Civic Newsroom](https://github.com/scottconverse/civic-newsroom) for the full background and the companion prompt-only toolkit.

## License

MIT — free to use, modify, and share.
