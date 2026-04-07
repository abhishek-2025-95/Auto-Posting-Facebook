# Content and Theme Per Page

Each sector in `config.json` or `sectors.json` controls **what** and **how** you post for that page. Focus on these fields to shape content and theme.

---

## Required for content

| Field | Purpose |
|-------|--------|
| **sector** | Display name for logs (e.g. "Bihar Pulse", "Real Estate"). |
| **theme** | The main subject of the page. Used in **captions** and **image prompts** so the same breaking news is angled for this audience. |
| **system_prompt** | The **persona** for the LLM: who it is writing as. Defines voice and expertise. |

### Only theme news (e.g. Bihar Pulse)

| Field | Purpose |
|-------|--------|
| **only_theme_news** | Set to **true** so this page gets **only** news that matches the theme. No other news is posted. For **Bihar Pulse**, the pipeline fetches Bihar-only news from all sources below; if none is found, the cycle is skipped. |

**Bihar Pulse — sources used (all Bihar-related):**
- **News API** — India (country=in), then filter to headlines mentioning Bihar or Patna.
- **Reddit** — Search for "Bihar" across Reddit; plus hot posts from r/india, r/IndianNews, r/IndiaSpeaks, r/bihar, r/patna (filtered to Bihar/Patna in title or text).
- **Government of Bihar** — Public announcements / press releases from CM Secretariat (cm.bihar.gov.in) and Bihar Raj Bhavan (governor.bih.nic.in) when available.

---

## Optional: refine content and visuals

| Field | Purpose |
|-------|--------|
| **tone** | How the caption should feel (e.g. "Professional but approachable", "Energetic and motivating", "Clear and analytical"). |
| **hashtag_focus** | Hashtags this page should favor (e.g. "#RealEstate #HomeBuying"). The model will include these where relevant and add more. |
| **visual_style** | Short guidance for the **image prompt** so visuals match the page (e.g. "Polished, high-end; when relevant, property or market visuals", "Energetic, dynamic; activity and health imagery when relevant"). |

---

## How it’s used

- **Caption:** Persona (`system_prompt`) + page theme (`theme`) + optional `tone` and `hashtag_focus` are combined so each post speaks to that page’s audience and fits its theme.
- **Image:** The same article can get a different image concept per page: `theme` and optional `visual_style` steer the image prompt (e.g. real estate vs fitness vs tech) so the picture fits the page’s content focus.

---

## Example: same news, three pages

One breaking story can produce:

- **Real Estate page:** Caption ties the news to housing, markets, or buying/selling; image prompt can lean toward property or market visuals when it fits.
- **Fitness page:** Caption angles toward health, routine, or motivation; image prompt can lean toward activity or wellness when it fits.
- **Tech page:** Caption focuses on tech/AI impact and analysis; image prompt can lean toward tech or data visuals when it fits.

Tuning **theme**, **system_prompt**, and optionally **tone**, **hashtag_focus**, and **visual_style** per sector is how you keep content and theme consistent per page.
