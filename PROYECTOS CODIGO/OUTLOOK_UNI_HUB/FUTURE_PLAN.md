# Future Plan: Outlook Uni Hub Optimization

As we look toward the next iteration of the Outlook Uni Hub, we need to focus on scalability, maintainability, and expanding our intelligent processing capabilities. The current architecture successfully addresses our initial requirements—automating email classification and calendar event generation—but it is tightly coupled and relies on synchronous, blocking operations.

## 1. Architectural Refactoring & Decoupling

Right now, the email ingestion, categorization, and attachment parsing logic are all bundled within `process_inbox`. We need to modularize this:

*   **Ingestion Service**: Decouple the Office365 polling into an isolated worker or event-driven webhook (Microsoft Graph Subscriptions). Polling is fine for a v1, but webhooks provide a much cleaner, near real-time response.
*   **Pipeline Architecture**: Implement a processing pipeline (e.g., using Celery or a lightweight message queue) so that when an email with a payload is received, it pushes an event. The categorization and PDF parsing should happen asynchronously.
*   **LLM Service Abstraction**: The Gemini integration works well but is hardcoded. We need a proper `LLMProvider` interface. This allows us to inject different models, mock the LLM in unit tests, and handle rate-limiting or fallback strategies more robustly.

## 2. Advanced Document Parsing

The current `pdfplumber` + Regex implementation for calendar events gets the job done for simple dates (`YYYY-MM-DD`), but academic syllabi are notoriously messy (e.g., "Midterm: Next Thursday" or "Finals Week: May 12th-16th").

*   **Semantic Date Extraction**: Let's leverage Gemini (or another LLM) not just for classification, but for entity extraction from the PDFs. We can pass the extracted text chunks to an LLM with a strict JSON schema prompt to return structured events `[{"event_name": "Midterm", "date": "2026-10-14"}]`.
*   **OCR Integration**: We will inevitably encounter scanned PDFs. Adding `pytesseract` or relying on a cloud vision API will ensure we don't silently fail on image-based documents.

## 3. Robust State Management

We currently rely on the `FileSystemTokenBackend`, which is sufficient for local development but poses security and scalability risks in a production environment.

*   **Credential Storage**: Move token management to a secure vault (Azure Key Vault or AWS Secrets Manager).
*   **Idempotency**: We should track `message_id`s in a local SQLite or Postgres database to prevent reprocessing the same emails if the app crashes mid-execution. Right now, checking if a file exists helps, but doesn't solve partial processing states.

## 4. Testing & CI/CD

There are no automated tests. Before we add more features, we need a solid testing baseline.

*   **Unit Tests**: Mock `O365.Account` and `google.generativeai` to test the routing logic and date extraction pure functions.
*   **Integration Tests**: Use a test tenant or mocked Graph API responses.
*   **Containerization**: Dockerize the application to ensure consistency between development and deployment environments.

In summary, the foundation is solid, but to move from a script to a product, we need to enforce separation of concerns, improve our parsing intelligence, and establish proper engineering hygiene.
