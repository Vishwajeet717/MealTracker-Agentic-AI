# UI Redesign Plan - MealTracker

## 1. Primary User Workflow and Visual Hierarchy
**Primary workflow**: User sets calorie budget, logs meals via chat or manual entry, views progress, reviews meal list, optionally uses image analyzer, checks agent trace for transparency.
**Visual hierarchy** (descending importance):
1. Chat input and messages (primary interaction)
2. Meal list (secondary, frequent glance)
3. Calorie budget/progress (key metric)
4. Agent trace (transparency, tertiary)
5. AI Core branding (decorative but informative)
6. Guidance panel (optional tips)

## 2. Layout Regions
### Desktop (min-width: 1024px)
- **Three-column layout** (left 25%, center 50%, right 25%)
  - **Left Column (Sidebar)**: AI Core (compact), Daily Progress (budget/consumed/remaining + progress bar), Guidance (minimal)
  - **Center Column (Main)**: Chat panel (messages, input, quick actions), takes most vertical space
  - **Right Column (Sidebar)**: Today's Meals (compact list with avatars), Agent Trace (collapsible timeline)
- All columns have consistent vertical padding; sticky headers for panels.
- Header spans full width at top (brand + system status) – may be hidden on scroll to maximize chat area.

### Mobile (max-width: 1023px)
- **Single column layout** stacking: Header → Left Sidebar (progress controls) → Chat → Right Sidebar (meals & trace as tabs or accordions)
- Left sidebar collapsible via hamburger menu? Actually we can make left column always visible but reduced height; or use bottom sheet for progress.
- Simpler: vertical stack: Header, Progress bar (full width), Chat, Meals (expandable), Trace (expandable).

## 3. Visual Language
### Typography
- **Font**: System UI (San Francisco, system-ui) with variable font support if available; fallback to -apple-system, BlinkMacSystemFont.
- **Sizes**: Base 16px (1rem). Headings: H1 2rem, H2 1.75rem, H3 1.5rem, body 1rem.
- **Tracking (letter-spacing)**: Size-specific:
  - Headings: -0.02em to -0.05em (tight)
  - Body: 0em
  - Captions: 0.02em (slightly open)
- **Line-height**: 1.5 for body, 1.2 for headings, 1.4 for captions.
- **Font weight**: Use semantic weights: Regular 400, Medium 500, Semi-bold 600, Bold 700.
- **Optical sizing**: Enable `font-optical-sizing: auto;` for system fonts.

### Color System
- **Palette** (dark mode default, with light mode support via prefers-color-scheme):
  - Background: #000000 (pure black) or #0A0A0A (near black)
  - Foreground: #FFFFFF (white) at 90% opacity for primary text, 60% for secondary
  - Accent: Vibrant but not neon: Apple Blue #0A84FF (for interactive elements), Apple Green #34C759 (success), Apple Red #FF3B30 (error), Apple Yellow #FF9500 (warning)
  - Semi-transparent layers: Background with blur: rgba(255,255,255,0.2) for light mode, rgba(0,0,0,0.3) for dark mode
  - Borders: Subtle: rgba(255,255,255,0.1) light mode, rgba(0,0,0,0.1) dark mode
  - Success/error states: Use accent colors with appropriate contrast.
- **Dynamic colors**: Use CSS custom properties that adapt to light/dark.

### Elevation and Depth
- Use **translucent material** for panels: background with backdrop-filter: blur(20px) (or 10px for smaller elements).
- Add subtle shadow: `box-shadow: 0 4px 20px rgba(0,0,0,0.25);` for floating panels.
- Layering: Header (top), panels (middle), floating action button? Not needed.
- For cards/meals items: slight elevation on hover/focus.

### Spacing
- Base 8px grid: 4,8,12,16,20,24,32,40,48,56,64px.
- Padding: 16px inside panels, 24px between sections.
- Horizontal padding between columns: 24px.
- Border radius: 12px for panels, 8px for buttons, 4px for small tags.

### Imagery and Icons
- Replace emoji meal icons with SF Symbols-inspired SVG icons (simple outline, consistent weight).
- Use template images for empty states.
- Ensure icons are accessible (aria-hidden if decorative, label if meaningful).

## 4. Component States
Each interactive component should define:
- **Idle**: Default appearance
- **Hover/Focus**: Subtle scale (0.98) or opacity change, focus ring (2px solid accent)
- **Active/Pressed**: Scale 0.95, brightness shift
- **Loading**: Spinner skeleton or pulse animation
- **Success**: Brief green glow, checkmark icon
- **Error**: Red shake, error icon
- **Empty**: Illustrative empty state with friendly text
- **Offline**: Grayed out, disconnected icon (if applicable)

Apply to buttons, input fields, chat bubbles, meal items, trace items.

## 5. Enhancing Meal and Calorie Information Scanability
- **Meal list**: Each meal item with left-aligned icon, food name (bold), calories (right-aligned), small timestamp (bottom). Use consistent height.
- **Calorie progress**: Large circular progress bar or pill-shaped bar with percentage inside; show budget/consumed/remaining as large numbers.
- **Highlight today's total**: Use accent color for consumed/remaining.
- **Meal grouping**: Optionally group by time (breakfast, lunch, dinner, snacks) with section headers.

## 6. Image Analysis Discoverability
- **Image analyzer panel**: Located below chat input or as a floating button that opens a sheet.
- **Design**: Button with camera icon + label "Analyze Food". Tapping opens a full-screen sheet with preview, analyze button, and results.
- **Flow**: Upload → preview → analyze → show detected foods with confidence → "Add to meals" button.
- **Make it visible**: Use a tab in right sidebar or a floating action button (FAB) bottom center.

## 7. Agent Trace Visualization
- **Timeline design**: Vertical trace list with each event as a node.
- **Node shape**: Small circle (4px) with line connecting; on hover/focus expand to show details.
- **Animation**: When new trace added, node pulses and line extends smoothly.
- **States**: Pending (outline), Active (filled pulsing), Complete (solid check), Failed (exclamation).
- **Details**: Slide-out panel on tap/click showing tool name, arguments, result, timestamps.
- **Reduce clutter**: Show last 5 traces expanded, older collapsed.

## 8. Keyboard Navigation, Focus, Semantics, Contrast, Reduced Motion
- **Keyboard**: Tab order follows visual order; visible focus outline (2px solid accent, offset 2px).
- **ARIA**: Proper labels for regions (role="region" aria-label), live regions for chat and trace (aria-live="polite").
- **Contrast**: Ensure all text meets 4.5:1 (AA) for normal text, 3:1 for large text.
- **Reduced motion**: @media (prefers-reduced-motion: reduce) replace springs/transitions with cross-fade (opacity 200ms), disable non-essential animations, keep micro-interactions if they don't cause vestibular disturbance.
- **Reduced transparency**: @media (prefers-reduced-transparency: reduce) increase background opacity, disable backdrop-filter.

## 9. Responsive Breakpoints
- **Desktop**: ≥1024px (three columns)
- **Tablet**: 768px–1023px (maybe two columns: left collapsed into top bar, center chat, right sidebar as bottom tabs)
- **Mobile**: <768px (single column stacked: header → progress → chat → meals (accordion) → trace (accordion))
- Use CSS grid with auto-fit or media queries.

## 10. Files to Change (smallest coherent set)
- **web/index.html**: Adjust structure for new layout, add missing elements (image analyzer button, trace nodes, etc.), ensure proper ARIA.
- **web/styles.css**: Rewrite using CSS variables for colors, typography, spacing, elevation, dark/light media queries, motion reductions.
- **web/app.js**: Minimal changes: add classes for new states, adjust DOM selectors if IDs/classes change, add event listeners for image analyzer, trace interactions.
- **Optional**: Add new SVG icons in web/icons/ and reference via <svg> or inline.

## 11. Validation Strategy
- Run existing tests: `pytest tests/ -v` to ensure backend unchanged.
- Manual verification:
  - Load http://localhost:8000/ on desktop and mobile browsers.
  - Check all flows: set budget, log meals, remove meals (via chat), image analyzer (if implemented), trace viewing.
  - Verify responsive layout at breakpoints.
  - Test keyboard navigation (Tab, Shift+Tab, Enter, Esc).
  - Test prefers-reduced-motion toggle in OS settings.
  - Test contrast using axe or manual inspection.
  - Ensure no console errors.
  - Confirm API payloads unchanged (session_id, message format).
- Use subagent reviewer to validate final implementation.

## 12. Next Steps
1. Wait for subagent reports (audit, accessibility) to inform refinements.
2. Implement design in web/styles.css and web/index.html.
3. Test and iterate.
4. Have subagent worker review for regressions.
5. Final verification.