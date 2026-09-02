# Future Roadmap: Gmail Morning Briefing

The current MVP gets the job done, but it's just scratching the surface of what a personalized daily briefing should be. Here is how we are going to evolve the architecture.

## Near Term: Smarter Parsing & Summarization
- Rip out the regex-based parsing and replace it with a lightweight local LLM or a specialized API call for actual semantic summarization. We need to stop pulling just the first few lines of an email and start extracting the actual *action items*.
- Implement a better heuristic for filtering out newsletters and promotional garbage that sneaks past the primary inbox filter.

## Mid Term: Multi-Modal Briefings
- Text is fine, but audio is better. Integrate a high-quality TTS engine (like ElevenLabs or similar) to generate an actual podcast-style audio file every morning. 
- Add Calendar integration. The briefing needs context—knowing that I have a 9 AM meeting makes an email from that client at 8:45 AM infinitely more important.

## Long Term: Interactive & Actionable
- Make the briefing actionable. If an email requires a quick "Yes/No", we should be able to trigger that reply directly from the briefing interface without opening Gmail.
- Build a feedback loop. If the user skips a certain type of summary consistently, the system should learn to deprioritize those in the future. 

We need to make sure the cron job that runs this is rock solid and has proper error handling. If the API rate limits hit, it should fail gracefully rather than crashing.
