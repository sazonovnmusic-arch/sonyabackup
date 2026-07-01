---
name: job-search-automation
description: Automate job search and cover letter generation via browser scraping. Covers hh.ru (API blocked, browser fallback), vacancy extraction, and personalized letter generation delivered to Telegram.
category: productivity
triggers:
  - "автоматизировать поиск вакансий"
  - "откликаться на вакансии"
  - "сопроводительное письмо"
  - "headhunter"
  - "hh.ru"
  - "поиск работы"
---

# Job Search Automation

## Overview
End-to-end pipeline: search → extract → generate → deliver. User reviews and manually submits.

## Platform: hh.ru

### API Status (CRITICAL)
- **Public API** (`api.hh.ru/vacancies`) returns **403 Forbidden** without OAuth.
- **OAuth for applicants was discontinued December 15, 2025.** Only employer/recruiter OAuth remains.
- **Verdict:** Browser scraping is the only viable automation path for applicants.

### Browser Scraping Workflow

#### 1. Search URL
```
https://hh.ru/search/vacancy?text=Media+Buyer&schedule=remote&salary_from=100000&only_with_salary=true
```

**Key parameters:**
- `text` — job title (URL-encoded)
- `schedule=remote` — remote work filter
- `salary_from` — minimum salary in **local currency (₽)**. USD filter does not work.
- `only_with_salary=true` — exclude vacancies without salary

#### 2. Extract Vacancy IDs
Vacancy titles on hh.ru are not wrapped in simple `<a>` tags. Use **console JS** to extract IDs from the raw page HTML:

```javascript
const html = document.body.innerHTML;
const matches = html.match(/vacancy\/(\d+)/g);
const ids = [...new Set(matches)].map(m => m.replace('vacancy/', ''));
```

#### 3. Navigate & Parse
For each ID, navigate to `https://hh.ru/vacancy/{id}` and extract:
- **Title**: `[data-qa="vacancy-title"]` or `<h1>`
- **Salary**: text node near title
- **Company**: `[data-qa="vacancy-company-name"]`
- **Responsibilities**: section after "Обязанности:"
- **Requirements**: section after "Требования:"
- **Conditions**: section after "Условия:"

#### 4. Generate Cover Letter

**User's style rules (enforce strictly):**
- **Direct, informal tone.** No "уважаемые работодатели", no formal fluff.
- **Short and specific.** 2-3 paragraphs max. Match user's experience to job requirements with concrete numbers/tools/verticals.
- **Do NOT explain why the user left previous jobs.** Just document experience factually.
- **Do NOT include obvious technical details** (pixels, antidetect, Events API, etc.) — assume the employer knows the basics.
- **Lead with relevance**, not with formalities.
- **Key phrase:** "запускал направления с нуля — от аудита продукта до стабильного залива" (note: user corrected from "литья" to "залива" — arb slang for stable traffic flow)
- **Signature:** Always end with `Телеграм для связи: @sazonovcpa`

**Structure:**
1. Hook: reference the specific vacancy and role
2. Experience match: connect user's background to stated requirements
3. Specific achievements: numbers, tools, verticals, scale ($X/day, team size)
4. Soft close: interest in discussion
5. Contact info (Telegram handle)

#### 5. Deliver
Compile into a batch message sent to user's Telegram. Format:

```
Вакансия: {title} — {company}
Зарплата: {salary}
Ссылка: {url}

Сопроводительное:
{generated_letter}
---
```

## Automation Pipeline (Cron Job)

```yaml
schedule: "0 9 * * *"  # daily at 9 AM
steps:
  1. Accept cookie banner if present (blocks interactions otherwise)
  2. Navigate to search URL with user filters
  3. Extract vacancy IDs via console JS match on /vacancy/(\d+)/
  4. Limit to top N (e.g., 10) to avoid rate limits
  5. For each vacancy ID:
     a. Navigate with random delay (5–15s)
     b. Parse title, company, salary, description sections
     c. Generate cover letter using user's resume context + job details
  6. Compile and send to Telegram
  7. Log searched/seen IDs to avoid duplicates
```

## Pitfalls

- **Bot detection:** hh.ru watches for rapid navigation. Insert random delays between page loads.
- **Cookie banner:** Must accept before interacting with filters or search.
- **Salary currency:** hh.ru filters in ₽. Convert user's USD requirement to ₽ (~90,000–100,000 ₽ for $1000).
- **Login walls:** Some vacancies hide full description behind login. Skip these or note "требуется вход".
- **Similar vacancies:** hh.ru injects "похожие вакансии" links with `/vacancy/` in URL. Filter out IDs from the sidebar by only collecting IDs that appear before a certain HTML marker, or dedupe by checking if the title matches the search query.
- **Telegram length:** Generated letters + metadata must stay under ~4000 chars.

## Cover Letter Adaptation Matrix

Adapt each letter to the specific vacancy:

| Vacancy type | What to emphasize |
|-------------|-------------------|
| Gambling/nutra | Gambling experience, high budgets, ROI, nutra funnels |
| TikTok Ads | TikTok launch experience, moderation training, creative adaptation |
| Facebook Ads | Scale experience ($2-3k/day), pixel/tracking, campaign optimization |
| E-commerce | Product audit, stable flow, pixel setup, conversion optimization |
| Team Lead / Head | Team building, training buyers, process documentation, launch setup |
| Percentage/revenue share | Interest in uncapped earning, scale potential, performance-driven |
| Affiliate/Traffic Manager | Multi-channel experience, postback, tracking, arbitrage background |

## Resume Context (Nikita — update as needed)

- 6+ years in digital marketing (Facebook, TikTok, VK, Telegram Ads)
- Launched directions from scratch: product audit → stable traffic flow ("от аудита продукта до стабильного залива")
- Scaled campaigns to $2-3k/day, positive ROI
- Verticals: nutra, gambling, e-commerce, subscriptions, home goods, auto services, services
- Tools: Keitaro, postback, Pixel, Events API (mention only if relevant, not by default)
- **Last project (June–July 2026):** TikTok direction launch for a team — built structure, connected agencies and farm department, trained buyers on TikTok moderation. Transferred processes to team after operational setup. Frame as project-based / launch consulting, not as a failure.
- Open to remote work
- Contact: Telegram @sazonovcpa

## References
- `references/hh-ru-extraction.js` — ready-to-use console JS snippets for ID extraction and DOM parsing
- `templates/cover-letter-prompt.txt` — LLM prompt template for cover letter generation
- `references/telegram-channel-monitoring.md` — why Telegram global search is blocked and the only viable monitoring path (known channel list + direct `t.me/s/CHANNEL` scraping)
- `references/daily-batch-config.md` — cron job setup and 20-vacancy search strategy

## Verification Checklist
- [ ] Single vacancy extraction works end-to-end before enabling cron
- [ ] Generated letter matches user's tone preferences (no formalities, no exit explanations)
- [ ] Salary filter correctly converted to local currency
- [ ] No duplicate vacancies across days (maintain seen-IDs log)
