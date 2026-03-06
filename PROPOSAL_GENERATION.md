# Proposal Generation

## Overview

When the intent is `PROPOSAL`, the chatbot guides the freelancer through providing project details, then calls the LLM to generate a complete, professional proposal document.

---

## Required and Optional Fields

| Field | Description | Required |
|---|---|---|
| Client Name | Name of the client or company | Yes |
| Project Title | Short name for the project | Yes |
| Project Description | What the project involves | Yes |
| Deliverables | What will be produced or delivered | Yes |
| Timeline | Expected duration or deadline | Yes |
| Freelancer Name | Name of the person submitting the proposal | Yes |
| Budget / Rate | Proposed fee or hourly rate | Optional |
| Freelancer Skills / Background | Relevant experience to include | Optional |

---

## Field Collection Flow

The chatbot collects fields conversationally. If the freelancer provides all fields in one message, no follow-up questions are needed. Otherwise, the bot asks for missing fields one at a time.

```
Freelancer: I need a proposal for a logo design for BrightLeaf
Bot: Who is the client contact name?
Freelancer: Sarah at BrightLeaf
Bot: What are the deliverables -- just the logo or brand identity too?
Freelancer: Logo + brand guidelines
Bot: What's your proposed timeline?
Freelancer: 2 weeks
Bot: And the budget?
Freelancer: $600 flat fee
Bot: Perfect. Generating your proposal now...
```

### Field Extraction from Freeform Text

Before asking for fields, the system extracts them from the initial message using the LLM:

```python
EXTRACT_PROMPT = """
Extract the following fields from this message if present.
Return as JSON. Use null for missing fields.

Fields: client_name, project_title, project_description, deliverables, timeline, budget, freelancer_name, freelancer_background

Message: "{message}"
"""
```

---

## Proposal Generation Prompt

```python
PROPOSAL_PROMPT = """
You are a professional proposal writer for a freelancer.
Generate a complete, professional project proposal using the details below.

Match the tone to the project type:
- Creative projects (design, content, branding): warm, expressive, client-focused
- Technical projects (development, software, data): clear, structured, competency-focused

Do NOT use placeholder text. Every section must use real, specific content from the brief.

---
Client Name: {client_name}
Project Title: {project_title}
Project Description: {project_description}
Deliverables: {deliverables}
Timeline: {timeline}
Budget: {budget}
Freelancer Name: {freelancer_name}
Freelancer Background: {freelancer_background}
---

The proposal must contain these sections in order:
1. Introduction
2. Project Understanding
3. Proposed Approach
4. Deliverables
5. Timeline
6. Pricing
7. Terms
8. Closing

Write in clear, professional English. Sound like a real person, not a template.
"""
```

---

## Proposal Document Structure

### 1. Introduction
Brief professional opening. Demonstrates that the freelancer understands the client's needs and establishes credibility.

### 2. Project Understanding
A summary of what the project involves, written back to the client in the freelancer's own words.

### 3. Proposed Approach
How the freelancer plans to tackle the work -- methodology, tools, process stages.

### 4. Deliverables
A clear, numbered or bulleted list of everything that will be produced.

### 5. Timeline
Proposed schedule or milestone breakdown with dates or durations.

### 6. Pricing
Total cost or rate breakdown. If budget was not provided, this section states "To Be Discussed."

### 7. Terms
Revision rounds, payment schedule (e.g. 50% upfront), ownership of deliverables, cancellation policy.

### 8. Closing
A professional sign-off inviting the client to proceed or schedule a call.

---

## Output and Download

After generation:
- The full proposal is displayed as a preview in the chat
- **Conversational Editing:** The freelancer can request changes (e.g., *"Make it more professional"*) and the bot will regenerate the draft.
- Download buttons are shown: **Download as PDF** and **Download as Word (.docx)**
- The proposal and project are saved to storage linked to the **ClientID**.
- Both PDF and Word files are generated/overwritten on every revision.

```python
storage.save_proposal({
    "client_id": client_id,
    "project_title": project_title,
    "project_description": project_description,
    "deliverables": deliverables,
    "timeline": timeline,
    "budget": budget,
    "freelancer_background": freelancer_background,
    "content": proposal_text,
    "created_at": datetime.now().isoformat(),
    "file_path": pdf_path
})
```

---

## Quality Validation

Before returning the proposal to chat, the system checks:
- All 8 sections are present in the output
- No placeholder text such as `[INSERT NAME]` or `TBD` exists in required fields
- Minimum word count of 300 words is met

If validation fails, the LLM is called again with a correction instruction.
