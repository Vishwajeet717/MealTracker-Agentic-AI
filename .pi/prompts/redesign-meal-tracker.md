---
description: Redesign the MealTracker UI with premium Apple-inspired UX
argument-hint: "[specific focus or constraint]"
---

You are the lead product designer and frontend engineer for this repository. Redesign the MealTracker web experience with a premium, calm, Apple-inspired level of craft while preserving the existing behavior and the educational purpose of the application.

The user may provide an extra focus or constraint here: ${@:-none}. Treat it as additive unless it conflicts with the repository's working behavior.

## Operating rules

1. Work inside the current repository. Do not invent a framework or migration unless the codebase clearly requires it.
2. The frontend is currently a vanilla HTML/CSS/JavaScript app in `web/`, served by FastAPI. Preserve the existing API contracts and session behavior.
3. Use the two required skills before designing or editing:
   - Run `npx skills use "https://github.com/nextlevelbuilder/ui-ux-pro-max-skill" --skill "ui-ux-pro-max"`.
   - Run `npx skills use "https://github.com/emilkowalski/skills" --skill "apple-design"`.
   Read the complete generated output and follow the instructions. Resolve any relative paths from the supporting-files directory named by each command.
4. Use the available subagents extension/mechanism for parallel research and review. Delegate at least:
   - one subagent to audit the current UI and interaction flows;
   - one subagent to review accessibility, responsive behavior, and motion performance;
   - one subagent to review the proposed implementation for regressions.
   Do not delegate the final decision blindly: reconcile their findings yourself.
5. Do not use placeholder UI, fake data, or a decorative redesign that hides working features. Keep the implementation testable and runnable.

## Phase 1: identify the product before planning

Before changing any file, inspect the repository and produce a concise feature inventory. Verify the inventory from source, not assumptions. Include:

- chat flow and loading/error states;
- session-scoped memory, calorie budget, consumed and remaining totals;
- meal list, meal removal, and estimated-versus-local calorie provenance;
- image upload, analysis, confirmation, and add-foods flow;
- live agent trace events and their meanings;
- API routes and the frontend/backend boundary;
- current responsive behavior, accessibility issues, and existing animation/performance costs;
- tests or checks that must remain green.

Write the inventory and a short list of UX problems to solve before implementation. Do not edit until this inspection is complete.

## Phase 2: plan the desktop-first experience

Create a concrete UI plan before coding. Design desktop-first, then define the mobile adaptation. The plan must specify:

- the primary user workflow and visual hierarchy;
- layout regions and what information belongs in each;
- a restrained, premium visual language with purposeful typography, strong spacing, tactile controls, and a distinct color system that is not a generic purple dashboard;
- component/state behavior for idle, typing, tool call, tool result, success, error, empty, and offline states;
- how the meal and calorie information becomes easier to scan;
- how image analysis is discoverable without competing with the primary chat workflow;
- how the trace becomes understandable to a human, including animated tool-call visualization;
- keyboard navigation, focus treatment, semantics, contrast, reduced-motion behavior, and responsive breakpoints;
- the smallest coherent set of files to change and the validation strategy.

Prefer a focused redesign of the existing product surface over adding a marketing landing page. Keep the first viewport useful and action-oriented.

## Phase 3: implement the redesign

Implement the approved plan in the existing frontend. Keep API payloads, route names, session IDs, and user-visible data semantics intact. Improve the experience through:

- clear hierarchy and calmer information density;
- premium typography and spacing using available web-safe or explicitly loaded fonts;
- responsive desktop and mobile layouts without horizontal overflow;
- polished empty, loading, error, and success states;
- accessible buttons, inputs, labels, live regions, and focus states;
- meaningful motion only: page entrance, message/meal reveal, trace step progression, and tool-call state transitions;
- an animated trace timeline where each event visibly progresses through pending, active, complete, or failed states, with concise labels and expandable details;
- `prefers-reduced-motion` support and no animation that blocks interaction or causes layout shift.

Use existing patterns where they are sound. Avoid unnecessary dependencies, nested cards, oversized hero sections, fake glassmorphism, excessive gradients, and ornamental animation that does not clarify state.

## Phase 4: verify the result

Run the repository's relevant tests and start the app using its documented command. Inspect the rendered UI at a wide desktop viewport and at a narrow mobile viewport. Capture a before/after screenshot if the environment supports it. Check:

- all existing flows still work against the real API;
- chat submission, loading, errors, and retries;
- budget and meal totals update correctly;
- image analysis and confirmation remain usable;
- trace events render in order and animate without flooding or jitter;
- keyboard and reduced-motion behavior;
- no console errors, broken asset paths, overflow, or unreadable text.

Have the subagent reviewer inspect the final diff and fix any concrete regression it finds. Finish with a concise report containing the feature inventory, implemented design decisions, files changed, validation commands/results, screenshot location if available, and any remaining limitations.
