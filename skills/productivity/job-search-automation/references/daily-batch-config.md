# Daily Batch Configuration — 20 Vacancies

## Cron Job Setup

```yaml
job_id: hh-vacancy-search
schedule: "0 6 * * *"  # 6:00 UTC = 9:00 MSK
deliver: origin  # Telegram
toolsets: [browser]
```

## Search Strategy (20 vacancies/day)

Run queries in order until 20 vacancies collected:

1. `Media Buyer` (remote, salary ≥100000₽, with salary only)
2. `TikTok Ads` (same filters)
3. `Facebook Ads` (same filters)
4. `таргетолог` (same filters)
5. `Traffic Manager` (same filters)
6. `Performance маркетолог` (same filters)
7. `Affiliate manager` (same filters)

URL template:
```
https://hh.ru/search/vacancy?text={QUERY}&schedule=remote&salary_from=100000&only_with_salary=true&order_by=publication_time
```

## Filtering Rules

### Include
- Any paid traffic / media buying role
- Team Lead / Head of advertising / marketing
- Performance roles with paid traffic focus
- Affiliate / traffic management roles

### Exclude
- Pure SMM (content posting, no paid ads)
- Pure SEO / ASO
- Design / copywriting (unless combined with media buying)
- Reger / farm account jobs (if primary role)
- HTML / верстальщик / дизайнер

## User Constraints
- User sends 20 applications/day manually (~30-40 min work)
- NEVER auto-click "Откликнуться" — account ban risk
- Cover letters: 2-3 paragraphs, direct tone, no formalities
