# Feature Inventory - MealTracker

## Core Features
1. **Chat Interface** - Conversational UI with the meal agent
   - User messages displayed on left, agent on right
   - Real-time typing indicator
   - Scroll-to-bottom on new messages
   - Message formatting (bold, line breaks)
   - Avatar labels (YOU, AI, MEAL AGENT)

2. **Meal Logging & Tracking**
   - Add meals via chat (using `add_meal` tool)
   - Manual meal button (pre-fills "I ate ")
   - Meal list in right sidebar showing food name, calories, timestamp, and estimation indicator
   - Meal removal (via `remove_meal` extension tool, not shown in UI? Actually there is no remove button in current UI; maybe it's via chat only)
   - Estimated meals marked with "EST." badge

3. **Calorie Budget Management**
   - Set budget via chat or quick action button
   - Display budget, consumed, remaining calories
   - Visual progress bar showing percentage of budget used

4. **Agent Trace Panel**
   - Shows step-by-step agent reasoning and tool calls
   - Each trace item includes title and detail (tool name, arguments, result)
   - Auto-scrolls to latest trace
   - Empty state message

5. **Quick Actions**
   - Predefined buttons: SET 2000 KCAL, CHECK STATUS, PLAN SNACK
   - Send predefined messages to agent

6. **Session Management**
   - UUID-based session ID stored in localStorage
   - State persistence per session via FastAPI endpoints

7. **API Endpoints**
   - GET /api/health - health check
   - GET /api/state?session_id= - get current state (budget, meals, totals)
   - POST /api/chat - send message, get reply, trace, state
   - POST /api/budget - set budget via agent

## Missing Features / Extension Tools
- Image analysis/upload (mentioned in README but not visible in current UI)
- Remove meal UI button (only available via chat command?)
- Image analyzer panel not present in index.html

## Technical Observations
- Frontend: vanilla HTML/CSS/JS, no framework
- Styling: custom CSS with CSS variables, gradients, glow effects
- Layout: three-column layout (left sidebar AI core, center chat, right sidebar meals + trace)
- Responsive behavior: not examined yet
- Accessibility: not examined yet
- Motion/animation: currently uses smooth scroll for chat and trace; no complex animations

## Files Involved
- web/index.html - main markup
- web/styles.css - styling
- web/app.js - frontend logic
- api_server.py - FastAPI backend
- app/agent.py - agent loop and tool execution
- app/tools.py - tool implementations (lookup_calories, add_meal, remove_meal)
- app/memory.py - session state storage
- app/config.py - configuration

## Current UI Description (from index.html)
- Dark background with cyan/blue/green glows
- Topbar with brand orb (AI), brand copy, system status
- Left column: AI Core panel (animated orb), Daily Progress panel (budget, consumed, remaining, progress bar), Guidance panel
- Center column: Chat panel with header, messages, quick actions, input form, footer
- Right column: Today's Meals panel (list, count, manual meal button), Agent Trace panel (trace list, live status)

## Notes
- The UI already has a fairly designed look with gradients and animated elements (background glows, orbiting AI core). This may be a existing design that needs to be redesigned per the prompt.
- The prompt asks to redesign with premium Apple-inspired UX, preserving existing behavior.

## UX Problems to Solve
1. **Visual Design** - Current UI uses neon cyberpunk glows and gradients, not aligned with Apple's premium, calm aesthetic. Needs refinement to a more restrained, tactile interface.
2. **Typography** - Uses monospace? Need to check; likely system default but not optimized for readability with proper tracking, leading, and optical sizing.
3. **Color System** - Current cyan/blue/green on dark background may not meet accessibility contrast ratios; Apple-inspired design would use more subtle, adaptive colors with proper light/dark mode support.
4. **Motion & Animation** - Limited to smooth scroll; lacks fluid, interruptible animations, spring-based feedback, velocity tracking, and material-like transitions.
5. **Accessibility** - Potential issues: focus rings, contrast, touch target size, ARIA labels, reduced motion support, reduced transparency support.
6. **Responsive Behavior** - Three-column layout may not adapt well to mobile; needs reflow to single column or appropriate breakpoints.
7. **Interaction Feedback** - Button feedback may be lacking (no active state, haptics/sound not applicable but visual feedback important).
8. **Information Hierarchy** - Panels may compete for visual weight; need to clarify primary workflow (chat) vs secondary info (meals, trace).
9. **Empty States** - Basic empty messages; could be more illustrative and friendly.
10. **Loading/Error States** - No explicit loading skeleton for chat messages or tool results; error handling limited to agent error messages.
11. **Touch Targets** - Buttons and interactive elements may be too small (<44x44px) for comfortable touch.
12. **Keyboard Navigation** - Tab order and focus visibility need verification.
13. **Material & Depth** - Lack of translucent layers, blur effects, and depth hierarchy that Apple uses to separate UI layers.
14. **Velocity Handoff** - No gesture-driven interactions (drag/swipe) but if added (e.g., swipe to delete meal) would need proper velocity tracking.
15. **Reduced Motion Support** - No media query prefers-reduced-motion handling; animations should switch to cross-fades.
16. **Spatial Consistency** - Transitions should enter/exit along same path; panel animations may not be symmetric.
17. **Iconography** - Uses emojis for meal icons; Apple design would use refined, symbolic icons with consistent stroke weight.
18. **Text Treatment** - No use of font-optical-sizing, variable fonts, or size-specific tracking/leading.
19. **Form Controls** - Chat input lacks proper label (uses aria-label but could be improved), placeholder text may not be sufficient.
20. **Scrolling Behavior** - Chat and trace scroll smoothly but may cause layout shift if not careful; need to reserve space.

These UX problems will guide the redesign in Phase 2.