# Updated UI Redesign Plan - MealTracker

## Design Decisions

### 1. Visual Language (Apple-inspired)
- **Theme**: Support both light and dark mode using `prefers-color-scheme`.
- **Color Palette** (adapted from ui-ux-pro-max search for accessibility and Apple vibe):
  - Primary: `#5E5CE6` (Viable for both modes, adjust on contrast)
  - Background: Dark mode: `#000000`, Light mode: `#FFFFFF`
  - Card/Surface: Dark mode: `#1C1C1E`, Light mode: `#F2F2F7` (Apple's system backgrounds)
  - Separator: Dark mode: `#38383A`, Light mode: `#E5E5E7`
  - Text: Dark mode: `#FFFFFF`, Light mode: `#000000`
  - Accent (for CTA): `#FF9500` (Apple Orange) or `#0A84FF` (Apple Blue)
  - Success: `#34C759`, Error: `#FF3B30`, Warning: `#FF9500`
  - Muted: `#8E8E93`
- **Translucency**: Use `background-color: rgba(255,255,255,0.1)` for dark mode surfaces and `rgba(0,0,0,0.1)` for light mode, with `backdrop-filter: blur(20px)`.
- **Typography**: 
  - Use Apple's system font: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif`.
  - For headings, consider using a variable font if available, but system font is sufficient.
  - Apply size-specific tracking (letter-spacing):
    - Headings: `-0.5px` to `-1px` (tight)
    - Body: `0px`
    - Captions: `0.5px`
  - Line-height: 1.4 for body, 1.2 for headings.
- **Icons**: Replace emoji meal icons with SF Symbols-inspired SVGs (we'll use simple geometric shapes or rely on system fonts for now, but avoid emojis).

### 2. Layout
- **Desktop (≥1024px)**: Three-column layout as before, but with adjusted widths:
  - Left sidebar: 260px (fixed)
  - Center: flexible (min 400px)
  - Right sidebar: 280px (fixed)
  - Gutter: 24px between columns.
- **Tablet (768px–1023px)**: 
  - Left sidebar collapses to top bar (height 60px) with icons for AI Core, Progress, Guidance (hidden labels, show on hover?).
  - Center: takes remaining width.
  - Right sidebar: bottom tabs (Meals, Trace) as accordions or segmented control.
- **Mobile (<768px)**: Single column stacked:
  - Header (compact)
  - Progress bar (full width, compact)
  - Chat (takes most space)
  - Meals and Trace as expandable sections below chat.
- **Responsive Breakpoints**: 375px, 768px, 1024px, 1440px (from pre-delivery checklist).

### 3. Components
- **Buttons**: 
  - Height: 44px minimum.
  - Border radius: 12px.
  - Background: translucent as described.
  - Hover: increase background opacity slightly.
  - Pressed: scale 0.97.
  - Focus: outline 2px solid accent color, offset 2px.
- **Input**: 
  - Height: 44px.
  - Padding: 12px horizontal.
  - Background: translucent.
  - Border: 1px solid separator color.
  - Border radius: 12px.
  - Focus: outline as button.
- **Cards/Panels**: 
  - Background: translucent.
  - Border radius: 16px.
  - Padding: 20px.
  - Box-shadow: 0 4px 24px rgba(0,0,0,0.2) for depth.
- **Meal List Item**:
  - Height: 56px (to meet touch target).
  - Display: flex, align items center.
  - Leading: icon (24x24).
  - Title: food name (truncate if needed).
  - Trailing: calories (e.g., "120 kcal").
  - If estimated, show a small dot or "est." badge.
  - Border radius: 12px.
  - Margin-bottom: 12px.
- **Progress Bar**:
  - Height: 8px.
  - Border radius: 4px.
  - Background: separator color.
  - Fill: accent color.
  - Animated width change.
- **Agent Trace**:
  - Timeline on left (2px wide, accent color).
  - Each event as a circle (8px diameter) on the timeline.
  - Event details to the right.
  - On hover/focus, expand to show full details.
  - Animation: when new event added, circle pulses and line extends.
- **Empty States**:
  - Illustrative (use SF Symbols-like icon or simple graphic).
  - Title and description.
  - Centered.

### 4. Motion & Animation (Apple Design Principles)
- **Response**: On press, immediate feedback (scale 0.97).
- **Direct Manipulation**: Not applicable as we have no drag interactions yet.
- **Interruptibility**: Use CSS transitions that can be interrupted (avoid animations that lock state).
- **Spring-like behavior**: For simplicity, use CSS transitions with cubic-bezier(0.4, 0.0, 0.2, 1) (Apple's ease-in-out).
- **Velocity Handoff**: Not applicable without gesture-driven interactions.
- **Momentum Projected**: Not applicable.
- **Spatial Consistency**: For panels that slide in/out, use same path.
- **Rubber Banding**: Not applicable.
- **Reduced Motion**: 
  - `@media (prefers-reduced-motion: reduce)`: 
    - Disable all non-essential animations.
    - Use cross-fade (opacity) for transitions.
    - Keep micro-interactions if they don't cause motion sickness (e.g., button press scale).
- **Reduced Transparency**: 
  - `@media (prefers-reduced-transparency: reduce)`: 
    - Increase background opacity of translucent surfaces to 1.0.
    - Disable backdrop-filter.

### 5. Accessibility Fixes (from reviewer)
- **Contrast**: Ensure all text meets 4.5:1. Use the colors above which are tested.
- **Touch Targets**: All interactive elements ≥44x44dp.
- **Responsive Flex**: Add `flex-direction: column` in ≤560px media query for left and right columns.
- **Smooth Scroll**: Detect prefers-reduced-motion and set behavior to 'auto' if reduced motion requested.
- **Skip Link**: Add a visually hidden skip-to-main link at the top of body.
- **Aria-label**: Add to quick buttons.

### 6. Addressing Researcher Weaknesses
- **Responsiveness**: Fix the truncated media query by completing the rules (we'll rewrite CSS).
- **Onboarding**: Add a help button or tooltip that shows example commands on first load (or via a modal).
- **Session History**: Not required for CA1, but we can note that it's out of scope. We'll keep current session only.
- **Trace Panel**: Simplify trace labels to be more user-friendly (e.g., "Thinking", "Checking calories", "Added meal"). Keep technical details available on expand.
- **Session Management**: Add a button to clear session (reset) in the settings (we can add a gear icon in header).

### 7. Files to Change
- **web/index.html**: 
  - Add skip link.
  - Update classes for new layout and components.
  - Add helper elements (e.g., for onboarding tooltip).
  - Change meal icons to SVG or remove emojis.
  - Add reset button in header (optional).
- **web/styles.css**: 
  - Rewrite completely with new design system, colors, typography, layout, components, motions, and media queries.
  - Include light/dark mode preferences.
  - Include reduced motion and reduced transparency handling.
- **web/app.js**: 
  - Update DOM selectors if classes changed.
  - Add smooth scroll behavior detection.
  - Add event listener for reset button (if added).
  - Update trace label mapping to user-friendly strings.
  - Add helper for onboarding (show once per session).

### 8. Validation
- Run existing tests: `pytest tests/ -v` to ensure backend unchanged.
- Manual testing on desktop and mobile browsers.
- Check contrast with axe or similar.
- Verify touch targets.
- Test keyboard navigation.
- Test reduced motion and reduced transparency settings.
- Verify API contracts unchanged.

### 9. Implementation Order
1. Update HTML structure and classes.
2. Rewrite CSS with new design.
3. Adjust JavaScript for changed selectors and new behaviors.
4. Test and iterate.
5. Run subagent reviewer for final check.

Let's begin by updating the HTML and CSS.

Note: We must preserve the existing behavior and API contracts.

We'll start by creating backup of the original files, then modify.

But first, let's output the plan to a file for reference.