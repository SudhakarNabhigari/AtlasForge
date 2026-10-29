# CA3 Mini Project 2 Report — AtlasForge

## 1. Project title
AtlasForge — AI Research & Knowledge Navigator

## 2. Objective and problem statement
The objective is to convert unstructured research text or a document into validated, structured knowledge. Research notes can make claims, methods, limitations, keywords, and research questions difficult to identify and search manually.

## 3. Selected automation idea
Convert a research paper or uploaded document into structured claims, methods, limitations, and keywords; extract research questions into a searchable knowledge base.

## 4. Workflow / architecture
User text or TXT/MD file → frontend → FastAPI extraction endpoint → Gemini structured JSON (if configured) or local fallback → Pydantic schema validation → user review → create/update API → SQLite database → frontend confirmation/library.

## 5. Technology stack
- Frontend: HTML, CSS, JavaScript
- Backend: Python, FastAPI
- Schema validation: Pydantic
- Database: SQLite
- AI integration: Gemini API via HTTPX (optional); local fallback when no API key is set

## 6. Schema
`title`, `summary`, `claims[]`, `methods[]`, `limitations[]`, `keywords[]`, `research_questions[]`, `source_text`.

## 7. Database design and operations
The `research_records` table stores title, summary, JSON arrays for extracted fields, source text, and timestamps. Create, read, update, and delete operations are provided. Review fields before saving and confirm before deletion.

## 8. Test evidence
Insert your own screenshots from the running application:
1. Input screen
2. Validated extraction output
3. Saved record in Knowledge library
4. Missing/invalid input message
5. Optional: updated record

## 9. Deployment
Public frontend URL: **[Add your actual deployed URL]**

## 10. Limitations
TXT/Markdown upload only; no PDF parsing or OCR; fallback extraction is heuristic; Gemini requires a valid API key; SQLite may not persist on ephemeral hosting.

## 11. Conclusion
AtlasForge demonstrates a full-stack schema-guided AI workflow from user input to validated structured output and database persistence, with a searchable knowledge library.
