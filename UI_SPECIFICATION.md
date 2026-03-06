# LUME UI/UX Specification: "The Editorial Glass"

## 1. Vision: "Lume-inance"
LUME isn't just a chatbot; it's a **living document**. The design moves away from the "message bubble" cliché towards an **EDITORIAL GRID** where information floats on a deep, interactive glass canvas.

---

## 2. Creative "Lume-inance" Elements
- **Dynamic Light Source:** A subtle, soft-glow orb follows the active message, creating a "Lume-inance" effect that shifts the glass reflections as the user types.
- **Progressive Depth:** 
  - **Background:** Static, deep matte finish (#0A0A0B).
  - **Mid-ground:** Translucent glass cards with `backdrop-filter: blur(25px)` for data summaries.
  - **Fore-ground:** High-clarity, ultra-thin glass for active chat interactions.

---

## 3. High-End Typography Pairing
- **The "Headline" (Headings):** `Playfair Display` (Black Italic) — used for client names and total amounts, making every invoice feel like a premium editorial cover.
- **The "Lead" (Subtitles):** `DM Mono` (Medium) — for technical details like [INV-1004], giving it a "stamped evidence" feel.
- **The "Copy" (Body):** `Outfit` or `Inter` (Light) — ultra-clean, widely tracked letters for that "high-end boutique" airiness.

---

## 4. Reimagined Components

### Beyond the Bubble: "The Floating Card"
- Instead of standard rounded bubbles, both Bot and User messages appear as **Editorial Cards**.
- **User Cards:** Ultra-minimalist, no background, just clean white text with a soft "glow-underline."
- **Bot Cards:** Suspended glass panels with a vertical "Navy Ink" or "Burgundy Urgent" bar that bleeds into the glass transparency.

### The "Inspection Overlay"
- When a document is generated, it doesn't just show a link. A **"Ghost-Preview"** appears— a faint, semi-transparent outline of the document that expands into a full-screen glass modal for inspection when hovered.

### Action Interaction: "The Ink Bleed"
- Buttons are not boxes. They are **Ink-on-Glass**. When hovered, the color (Navy or Burgundy) "bleeds" into the glass container, turning it from translucent to a rich, solid brand color with a 0.2s transition.

---

## 5. Movement & Soul
- **Staggered Entrance:** Message elements (Header, Body, Actions) don't appear at once. They follow a 0.05s staggered "Ink Flow" animation.
- **Soft-Response Glow:** When LUME is processing, the entire background border pulse-glows in Navy, mimicking a steady breath.
