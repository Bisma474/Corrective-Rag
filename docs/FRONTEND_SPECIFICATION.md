# Frontend Specification Document

## 1. Design Principles
- **Modern & Immersive**: Dark mode by default, utilizing glassmorphism (translucent panels, subtle drop-shadows, and background blur).
- **Responsive**: Adapts gracefully to desktop, tablet, and mobile layouts.
- **Action-Oriented & Readable**: Modern geometric typography (`Inter` or `Outfit` fonts) with clear separation of local versus search engine citation sources.

---

## 2. Design System

### Colors
- **Background**: `#0b0f19` (Deep Obsidian Space)
- **Cards/Surfaces**: `rgba(20, 26, 42, 0.65)` with backdrop-filter blur `12px`
- **Primary Color**: `#6366f1` (Indigo Glow)
- **Secondary Color**: `#14b8a6` (Teal Aurora)
- **Text Primary**: `#f8fafc` (Off-white)
- **Text Secondary**: `#94a3b8` (Muted Slate)
- **Status Colors**:
  - *Correct / Pass*: `#10b981` (Emerald)
  - *Incorrect / Fallback Web Search*: `#f59e0b` (Amber)
  - *Error / Alert*: `#ef4444` (Ruby)

### Typography
- **Primary Font**: `Outfit`, sans-serif (imported via Google Fonts)
- **Sizes**:
  - H1: `2.25rem`
  - H2: `1.5rem`
  - Body: `0.975rem`
  - Code/Log: `0.85rem`

---

## 3. Layout System
- **Sidebar**: Fixed width `280px` containing user workspace, upload zone, and past chat threads.
- **Main Chat Grid**: Centered interface with a max-width of `850px` for optimal reading flow.
- **Log Visualizer Pane**: Collapsible sliding drawer on the right side of the chat showing live agent steps.

---

## 4. Component Specifications

### Buttons
- Translucent border buttons with subtle linear gradient transitions on hover.
- Ripple and micro-scaling effects (`scale(0.97)`) on click events.

### Inputs
- Full-width dark search bar container, featuring glow effects when focused (`box-shadow: 0 0 10px rgba(99, 102, 241, 0.4)`).

### CRAG Agent Pipeline Visualizer
- Graphical stepper showing steps:
  1. `RETRIEVAL`: Green (success) or orange (no results).
  2. `EVALUATOR`: Shows rating metric (e.g. relevance score: `0.15` - Failed).
  3. `SEARCH FALLBACK`: Web icon indicator indicating DuckDuckGo search queries executed.
  4. `GENERATOR`: Flashing pulse animation while token streaming is active.

---

## 5. Screen Specifications
- **Dashboard / Ingestion Screen**: Dropzone for files, list of active files with options to delete.
- **Chat Workspace**: Immersive chat history stream, real-time message response indicator, source citations.

---

## 6. Frontend Folder Structure
```text
frontend/src/
├── components/
│   ├── Sidebar.jsx
│   ├── ChatWindow.jsx
│   ├── PipelineLogs.jsx
│   └── DocumentManager.jsx
├── styles/
│   ├── index.css          # Design System core styles
│   └── components.css     # CSS Modules for components
├── App.jsx
└── main.jsx
```
