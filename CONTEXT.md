# TruthGuard Project Standards

This document establishes the 6 core development and design standards for TruthGuard. All agents, tools, utilities, and tests must strictly adhere to these rules.

## Core Standards

### 1. Structured Output Only
All agents return structured JSON. Never return free-form text. All agents must define their response models using Pydantic or typed dictionaries and enforce structured outputs.

### 2. Ephemeral Storage (No Persistence)
No user data is stored persistently. All temp files (such as uploaded images, intermediate evidence bundles, and reports) must be deleted after each session.

### 3. PII Screening
All LLM inputs must pass through `security.py` PII screening before processing. This ensures no names, email addresses, phone numbers, or other sensitive details are accidentally sent to external APIs.

### 4. Consolidated Gemini Access
All Gemini API calls go through `gemini_client.py` — never call the model or initialization routines directly. This allows centralized management of rate limits, retry backoff logic, and model selection.

### 5. Type Hints and Documentation
Every function has a docstring and complete type hints. The code must pass type checks and linting without warnings.

### 6. Structured Error Handling
All errors are caught and returned as structured error JSON. Never raise raw exceptions to the agent framework or the end-user.
