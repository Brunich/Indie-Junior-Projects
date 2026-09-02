# Future Plan: Business Voice WhatsApp

Hey team,

Here's the roadmap for where we need to take this WhatsApp voice bot next. The current MVP uses Playwright, Coqui TTS, and Gemini, which gets the job done for a proof-of-concept, but we have some technical debt and scalability bottlenecks to address before we can deploy this to production.

## 1. Move off Playwright (ASAP)
Right now, we're relying on browser automation for WhatsApp Web. It's flaky, consumes way too much memory, and breaks whenever Meta pushes a DOM update. 
*   **Action item:** We need to migrate to the official WhatsApp Business API (Cloud API) or a reliable robust provider like Baileys (Node.js) / WAPython. This will give us webhooks instead of having to poll the DOM for new messages.

## 2. TTS Optimization & Caching
Coqui TTS is heavy and running inference locally for every single message is going to nuke our server costs. 
*   **Action item:** Set up an async task queue (Celery/Redis or similar). 
*   **Action item:** Implement a caching layer. A lot of standard greetings/responses will be identical. Hash the translated text, check Redis, and serve the pre-generated `.wav` if it exists. 
*   **Action item:** Look into optimizing the model with ONNX or TensorRT, or consider offloading to a managed service like ElevenLabs if local hosting becomes too expensive/slow.

## 3. Context Management & LLM
Right now, the Gemini integration is stateless. It just answers the current message.
*   **Action item:** Implement conversation history tracking (LangChain or just simple SQLite/Postgres DB for message logs). 
*   **Action item:** System prompts need to be refined and injected dynamically based on the customer's profile or previous interactions.
*   **Action item:** Put a guardrail in place. We don't want the bot hallucinating business promises or giving away discounts that don't exist.

## 4. Multi-Tenant Architecture
If we're going to offer this to multiple businesses, hardcoding the `sample.wav` and business rules won't fly.
*   **Action item:** Design a proper DB schema linking a `BusinessID` to its specific TTS sample, system prompt, and API keys.

Let's knock out the Playwright migration first, that's the biggest risk factor right now. I'll set up a sprint board for these tasks next week.
