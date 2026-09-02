# Future Plan: Survey Population Bot

## Current State
The project currently supports basic automated form filling using Playwright and pandas. It reads from a static CSV file to populate demographic and preference-based fields. If data is unavailable, it gracefully falls back to synthetic generation while logging the appropriate warnings.

## Roadmap

### Phase 1: Robust Element Targeting
- **Implement Heuristic Selectors:** Move away from hardcoded CSS selectors or XPaths. Use natural language processing (or simple regex heuristics) on labels to identify input fields across different survey platforms (Google Forms, SurveyMonkey, Typeform).
- **Shadow DOM Support:** Ensure the bot can interact with complex web components commonly used in modern survey platforms.

### Phase 2: Enhanced Data Generation & Management
- **Dynamic Data Sources:** Integrate with external APIs (like Faker or randomuser.me) to generate vast, realistic datasets on the fly without relying entirely on static CSVs.
- **Database Integration:** Move from CSV to a lightweight database like SQLite or PostgreSQL for better state management and querying of used/unused profiles.
- **Data Validation Pipeline:** Implement schema validation (e.g., using Pydantic) to ensure the imported data matches the expected format before the bot attempts to use it.

### Phase 3: Proxy and Fingerprint Management
- **Proxy Rotation:** Integrate a proxy pool to avoid IP bans when submitting large volumes of surveys.
- **Browser Fingerprinting:** Implement stealth plugins (like `playwright-stealth`) to bypass bot detection mechanisms. Vary user agents, viewport sizes, and hardware concurrency settings per session.
- **Delay Randomization:** Add intelligent, randomized delays between keystrokes and clicks to mimic human behavior more accurately.

### Phase 4: CI/CD & Deployment
- **Dockerization:** Containerize the application for easy deployment across different environments.
- **Headless Cloud Execution:** Set up GitHub Actions or AWS Lambda/Fargate to run the bot on a schedule or via webhooks.
- **Monitoring & Alerting:** Integrate logging with services like Datadog or Sentry to track success rates, CAPTCHA encounters, and crash reports.

## Maintenance Notes
Keep Playwright and its browser binaries updated regularly to ensure compatibility with the latest web standards and to minimize detection risks. Monitor changes in the DOM structures of major survey providers.
