# Future Roadmap: Speedrun Exam Simulator

The core loop of taking an exam as fast as possible is fun, but to increase retention and replayability, we need to add more competitive features and stabilize the backend.

## Phase 1: Competitive Ecosystem
- Ship the global leaderboards. We need real-time syncing of scores, segmented by exam difficulty and category.
- Implement ghost runs. Let players race against the input replay of the current world record holder for a specific exam.
- Add "seasons" or weekly challenges with curated, randomized question pools to keep the community engaged.

## Phase 2: Content & Anti-Cheat
- The question pool is too static right now. Build a scraper or integration with an external API (like OpenTDB or custom educational datasets) to dynamically generate new questions.
- We need to address the cheating problem. Implement server-side validation of response times. If a user answers a 50-word question in 100ms, flag the run. 

## Phase 3: Engine Optimization
- Refactor the frontend state management. The slight jitter when advancing to the next question is unacceptable for a speedrunning tool. We need to pre-fetch the next 5 questions into memory.
- Move the backend from the current REST setup to WebSockets for the actual exam sessions to reduce latency overhead on answer submission. 

Performance is the feature here. If the app feels sluggish, the speedrun aspect is completely ruined.
