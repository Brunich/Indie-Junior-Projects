# Project Roadmap: WhatsApp Ticket Hunter

## Current State Architecture
Currently, the service runs as a monolithic Playwright automation script heavily dependent on DOM selectors for WhatsApp Web. This serves as a solid proof of concept but carries technical debt related to fragility (DOM updates) and scalability (single-threaded synchronous blocking). 

## Phase 1: Hardening & Reliability (Short-term)
* **Selector Abstraction:** Extract all CSS/XPath selectors into a dedicated configuration file (`selectors.json` or `config.yaml`). WhatsApp frequently mutates DOM classes for obfuscation; isolating these prevents core logic modifications during maintenance.
* **Session Persistence:** Implement browser context persistence (saving session state/cookies to disk). Re-scanning QR codes on every execution is unacceptable for a production-grade automation tool. 
* **Exception Handling & Retries:** Implement exponential backoff for network requests and DOM queries. Add fallback locator strategies (e.g., visual text matching if role-based locators fail) for ticketing sites.

## Phase 2: Decoupling & Concurrency (Medium-term)
* **Async IO:** Migrate from `playwright.sync_api` to `playwright.async_api`. This allows us to handle multiple URLs and inbound messages concurrently without blocking the main event loop.
* **Decoupled Architecture:** 
  * **Listener Node:** A dedicated process/thread solely responsible for reading incoming WhatsApp messages and enqueuing them to a message broker (e.g., Redis, RabbitMQ).
  * **Worker Nodes:** Background consumer workers that pop URLs from the queue, spin up headless contexts, and execute the actual hunting logic.
* **Webhook / API Alternative:** Evaluate migrating the WhatsApp listener from DOM scraping to a dedicated API provider (e.g., Twilio, Meta Cloud API, or Baileys for Node.js if rewriting the listener) to eliminate UI fragility completely.

## Phase 3: Advanced Evasion & Scale (Long-term)
* **Anti-Bot Mitigation:** Ticketing sites aggressively employ Cloudflare, Datadome, or PerimeterX. We need to integrate stealth plugins (`playwright-stealth`) or residential proxy rotators to maintain high success rates.
* **Containerization:** Dockerize the application. Use base images equipped with xvfb for headless browser execution in Linux environments, enabling easy deployment to AWS/GCP.
* **Telemetry & Logging:** Replace standard print statements with structured logging (JSON format). Integrate a telemetry stack (ELK or Datadog) to monitor success rates, button discovery latency, and DOM failure anomalies in real-time.

## Design Philosophy
We prioritize speed to click and stealth. Any millisecond wasted on unnecessary DOM parsing on the target ticketing site reduces conversion probability. Keep the hunting module aggressively optimized and strictly isolated from the messaging bus.
