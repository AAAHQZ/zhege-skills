---
name: brainstorming
description: "You MUST use this before any creative work - creating features, building components, adding functionality, or modifying behavior. Explores user intent, requirements and design before implementation. Architectural work produces a draft spec that feeds the to-spec skill."
triggers:
  - brainstorming
  - 头脑风暴
  - 设计讨论
  - 需求探索
  - 需求讨论
  - 方案设计
  - 功能设计
  - 架构设计
  - 写规格
  - spec 草稿
---

# Brainstorming Ideas Into Designs

Help turn ideas into fully formed designs and specs through natural collaborative dialogue.

Start by classifying how much process the request needs, then work
through your path: understand the context, refine the idea, present a
design, and get your human partner's approval. Architectural work ends with
a **draft spec** that the `to-spec` skill synthesizes and publishes; the draft
can first be stress-tested with `grilling` or `grill-with-docs`.

## Establish Shared Understanding

The outcome of brainstorming is an understanding your human partner can
recognize and correct, grounded in what they want to accomplish.

1. **Discover intent.** Use the request and available context to identify
   the intended outcome, who it is for, and what success looks like. When
   that information is missing, ask one focused question about purpose or
   intended use before proposing features or an approach. Knowing the app
   genre does not tell you why your partner wants it. Gathering missing
   requirements does not ask them to authorize the task again.
2. **Write back your understanding.** Summarize the intended outcome,
   relevant constraints, and success criteria in a short note your partner
   can assess. Separate what they said from assumptions. Invite correction
   and incorporate their answer before treating this as the design brief.
3. **Carry intent into the design.** Preserve the agreed understanding in
   the selected path's design artifact: the draft spec for architectural
   work, or the in-chat design/probe for bounded work and spikes. Check
   proposed features and technical choices against that understanding.

When the request already supplies the purpose and constraints, reflect
that understanding instead of asking the same questions again. Keep the
note concise; its accuracy and the opportunity to correct it matter.

<HARD-GATE>
Before taking any implementation action, including invoking an
implementation skill, writing product code, scaffolding, installing
product dependencies, or creating an external project, complete the
selected path's prerequisites:

- Spike: the human partner approves the question and probe.
- Bounded: the human partner approves the short in-chat design.
- Architectural: the human partner approves the design, then approves the
  draft spec (after optional grilling) before it is finalized through the
  `to-spec` skill. Conversational design approval only permits drafting the
  spec; draft approval permits the to-spec handoff. No implementation begins
  until the spec is finalized.

A reply approves the stage actually presented. Approval of an idea or
feature scope does not approve artifacts that do not exist yet. Resume
at the earliest incomplete stage; do not turn one approval into permission
to skip the rest of the selected path. Read-only project exploration is
allowed while those prerequisites remain incomplete.
</HARD-GATE>

## Three Paths

Before your first question, classify the request and say the
classification out loud — "this looks bounded, so I'll present a short
design here rather than write a spec" — so your human partner can
override it:

- **Spike** — a feasibility question ("can we...", "is it possible...",
  "quick and dirty is fine") whose output is an answer, not code you
  keep. Present the question and what you'll try in 2-3 sentences, get
  a nod, then find out as cheaply as correctness allows. No design
  doc, no spec file. Report findings as a recommendation; anything you
  built stays labeled throwaway.
- **Bounded** — a well-scoped change to code that already exists in
  this repo: a new flag, a small endpoint, a one-file fix.
  Understanding the kind of app is not enough — bounded means the flow
  you are changing is already here to read. If there is no existing
  flow to change, the task is not bounded. Ask the clarifying
  questions that matter, present a short design IN CHAT (a few
  sentences to a few short paragraphs), and STOP. Implementation
  starts only after your human partner says yes to that design — a
  bounded task's approval is as hard a gate as an architectural
  one. No spec file, no implementation plan document.
- **Architectural** — new projects, new subsystems, changes that
  restructure how components fit together or alter interfaces others
  depend on. Follow the full process: questions, approaches, sectioned
  design, a draft spec, optional grilling, then hand off to the `to-spec`
  skill to finalize and publish.

When in doubt between two paths, take the heavier one. The ratchet is
one-way: hidden complexity discovered mid-task upgrades the path —
stop, say so, and step up. Nothing downgrades mid-task.

## Anti-Pattern: "Too Simple To Need Approval"

Every path ends with your human partner approving the required design
before implementation. A bounded change may need only two sentences in
chat. A new todo-list project is architectural and requires a draft spec,
optional grilling, and the `to-spec` handoff. Scale the artifact to the
selected path; complete that path's reviews before implementation.

## Red Flags

| Thought | Reality |
|---------|---------|
| "This is too simple to need a design" | Follow the selected path: a bounded change gets a short chat design; an architectural change gets the draft spec and the to-spec handoff. |
| "I'll call it bounded and skip the spec" | Reaching for a label to skip work IS the doubt — take the heavier path. |
| "It's bounded and the design is obvious — I'll start while they read it" | The gate is the approval, not the design's length. Present, then stop until you hear yes. |
| "I understand this kind of app, so it's bounded" | Bounded measures the repo, not your familiarity. A new project has no existing flow — it is architectural. |
| "The spike works, so I'll keep the code" | A spike's output is an answer. Keeping the code is a new request — classify it. |
| "It grew, but I'm almost done — no need to re-classify" | Hidden complexity upgrades the path mid-task. Stop and say so. |
| "They approved the spike, so the follow-up change is approved too" | Each task gets its own classification and its own approval. |
| "The draft is done, so I'll start coding" | `to-spec` finalizes and publishes the spec first. Implementation starts only after that. |

## Checklist

Classify first, announce the path, then create a task for each item on
your path and complete them in order.

**Spike:**
1. **Explore project context** — enough to frame the probe
2. **Present question + probe plan** — 2-3 sentences
3. **Get approval** — a nod is enough
4. **Investigate** — as cheaply as correctness allows
5. **Report findings** — a recommendation; label anything built as throwaway

**Bounded:**
1. **Explore project context** — check files, docs, recent commits
2. **Ask clarifying questions** — one at a time, the ones that matter
3. **Present short design in chat** — approach, files touched, testing
4. **Get approval** — STOP and wait for an explicit yes; presenting the design and starting in the same breath is skipping the gate
5. **Implement** — proceed with the normal development workflow (TDD applies); no plan document

**Architectural:**
1. **Explore project context** — check files, docs, recent commits
2. **Ask clarifying questions** — one at a time, understand purpose/constraints/success criteria
3. **Propose 2-3 approaches** — with trade-offs and your recommendation
4. **Present design** — in sections scaled to their complexity, get user approval after each section
5. **Draft the spec** — write a draft in the `to-spec` shape (Problem / Solution / User Stories / Implementation Decisions / Testing Decisions / Out of Scope / Further Notes); keep it in chat or a working file
6. **Draft self-review** — quick inline check for placeholders, contradictions, ambiguity, scope (see below)
7. **Grill the draft (optional)** — offer `grilling` (or `grill-with-docs` to also produce ADRs and a glossary); on approval, invoke it and fold the answers back into the draft
8. **Hand off to `to-spec`** — invoke the `to-spec` skill to synthesize and publish the spec; if `to-spec` is unavailable, write the spec to `docs/specs/YYYY-MM-DD-<topic>-design.md` and ask the user to review it

## Process Flow

```dot
digraph brainstorming {
    "Classify: spike / bounded / architectural" [shape=diamond];
    "Present question + probe (2-3 sentences)" [shape=box];
    "Ask clarifying questions (bounded)" [shape=box];
    "Present short design in chat" [shape=box];
    "Human approves?" [shape=diamond];
    "Investigate; report recommendation" [shape=doublecircle];
    "Implement via normal workflow (no plan doc)" [shape=doublecircle];
    "Explore project context" [shape=box];
    "Ask clarifying questions" [shape=box];
    "Propose 2-3 approaches" [shape=box];
    "Present design sections" [shape=box];
    "User approves design?" [shape=diamond];
    "Draft the spec" [shape=box];
    "Draft self-review\n(fix inline)" [shape=box];
    "Grill the draft?\n(optional)" [shape=diamond];
    "Hand off to to-spec\n(finalize + publish)" [shape=doublecircle];
    "Hidden complexity? Upgrade path" [shape=box];

    "Classify: spike / bounded / architectural" -> "Present question + probe (2-3 sentences)" [label="spike"];
    "Classify: spike / bounded / architectural" -> "Ask clarifying questions (bounded)" [label="bounded"];
    "Classify: spike / bounded / architectural" -> "Explore project context" [label="architectural"];
    "Present question + probe (2-3 sentences)" -> "Human approves?";
    "Ask clarifying questions (bounded)" -> "Present short design in chat";
    "Present short design in chat" -> "Human approves?";
    "Human approves?" -> "Investigate; report recommendation" [label="spike: yes"];
    "Human approves?" -> "Implement via normal workflow (no plan doc)" [label="bounded: yes"];
    "Hidden complexity? Upgrade path" -> "Classify: spike / bounded / architectural";
    "Explore project context" -> "Ask clarifying questions";
    "Ask clarifying questions" -> "Propose 2-3 approaches";
    "Propose 2-3 approaches" -> "Present design sections";
    "Present design sections" -> "User approves design?";
    "User approves design?" -> "Present design sections" [label="no, revise"];
    "User approves design?" -> "Draft the spec" [label="yes"];
    "Draft the spec" -> "Draft self-review\n(fix inline)";
    "Draft self-review\n(fix inline)" -> "Grill the draft?\n(optional)";
    "Grill the draft?\n(optional)" -> "Draft the spec" [label="changes from grilling"];
    "Grill the draft?\n(optional)" -> "Hand off to to-spec\n(finalize + publish)" [label="ready"];
}
```

**Terminal states are path-bound.** Architectural: after brainstorming the
spec is finalized and published through `to-spec` — never jump straight from
the design conversation into implementation code. Bounded: after
approval, implementation proceeds directly through the normal
development workflow; no plan document. Spike: the terminal state is a
reported recommendation.

## The Process

The subsections below serve the bounded and architectural paths (a
spike stops at "present the probe, get a nod"). Sections from
**Exploring approaches** onward are architectural-path depth — for
bounded work, context plus a few questions plus a short in-chat design
is the whole process.

**Understanding the idea:**

- Check out the current project state first (files, docs, recent commits)
- Before asking detailed questions, assess scope: if the request describes multiple independent subsystems (e.g., "build a platform with chat, file storage, billing, and analytics"), flag this immediately. Don't spend questions refining details of a project that needs to be decomposed first.
- If the project is too large for a single spec, help the user decompose into sub-projects: what are the independent pieces, how do they relate, what order should they be built? Then brainstorm the first sub-project through the normal design flow. Each sub-project gets its own draft spec → `to-spec` → implementation cycle.
- For appropriately-scoped projects, ask questions one at a time to refine the idea
- Prefer multiple choice questions when possible, but open-ended is fine too
- Only one question per message - if a topic needs more exploration, break it into multiple questions
- Focus on understanding: purpose, constraints, success criteria

**Exploring approaches:**

- Propose 2-3 different approaches with trade-offs
- Present options conversationally with your recommendation and reasoning
- Lead with your recommended option and explain why
- YAGNI ruthlessly - remove unnecessary features from every approach and design

**Presenting the design:**

- Once you believe you understand what you're building, present the design
- Scale each section to its complexity: a few sentences if straightforward, up to 200-300 words if nuanced
- Ask after each section whether it looks right so far
- Cover: architecture, components, data flow, error handling, testing
- Be ready to go back and clarify if something doesn't make sense

**Design for isolation and clarity:**

- Break the system into smaller units that each have one clear purpose, communicate through well-defined interfaces, and can be understood and tested independently
- For each unit, you should be able to answer: what does it do, how do you use it, and what does it depend on?
- Can someone understand what a unit does without reading its internals? Can you change the internals without breaking consumers? If not, the boundaries need work.
- Smaller, well-bounded units are also easier for you to work with - you reason better about code you can hold in context at once, and your edits are more reliable when files are focused. When a file grows large, that's often a signal that it's doing too much.

**Working in existing codebases:**

- Explore the current structure before proposing changes. Follow existing patterns.
- Where existing code has problems that affect the work (e.g., a file that's grown too large, unclear boundaries, tangled responsibilities), include targeted improvements as part of the design - the way a good developer improves code they're working in.
- Don't propose unrelated refactoring. Stay focused on what serves the current goal.

## Drafting the Spec (architectural path)

Brainstorming's architectural output is a **draft spec**, not the final one.
The draft is what `to-spec` synthesizes and publishes.

**Draft the spec.** Use the `to-spec` shape so the handoff is mechanical:

- **Problem Statement** — the problem from the user's perspective
- **Solution** — the solution from the user's perspective
- **User Stories** — a long numbered list, "As an <actor>, I want a <feature>, so that <benefit>"
- **Implementation Decisions** — modules, interfaces, schema, API contracts, interactions (no file paths or code snippets)
- **Testing Decisions** — what makes a good test, which modules, prior art
- **Out of Scope**
- **Further Notes**

Keep the draft in chat, or in a working file if the conversation is long. Do
not commit it as the final spec — that is `to-spec`'s job.

**Draft self-review.** Look at the draft with fresh eyes:

1. **Placeholder scan:** Any "TBD", "TODO", incomplete sections, or vague requirements? Fix them.
2. **Internal consistency:** Do any sections contradict each other? Does the architecture match the feature descriptions?
3. **Scope check:** Is this focused enough for a single spec, or does it need decomposition?
4. **Ambiguity check:** Could any requirement be interpreted two different ways? If so, pick one and make it explicit.

Fix any issues inline. No need to re-review — just fix and move on.

For a deeper, independent check, dispatch a subagent using
`spec-document-reviewer-prompt.md` (in this skill's directory) before the
grilling step.

**Grill the draft (optional).** A draft is easier to attack than a blank page.
Offer the user a stress-test pass:

- `grilling` — relentless interview that maps the design tree and closes every open decision.
- `grill-with-docs` — the same, and it also produces ADRs and glossary entries as it goes.

> "The draft is ready. Want me to grill it before we finalize? I can run
> `grilling`, or `grill-with-docs` if you also want ADRs and a glossary."

On approval, invoke the named skill and fold its answers back into the draft.
If neither skill is available, offer to run the same rounds by hand. Skip this
step entirely if the user declines — it is an enhancement, not a gate.

**Hand off to `to-spec`.** When the draft is settled, invoke the `to-spec`
skill to synthesize the conversation and publish the spec to the issue tracker
(`to-spec` does not interview — brainstorming has already done that). `to-spec`
needs the issue tracker and triage label vocabulary configured; if it is not
set up, tell the user to run `/setup-matt-pocock-skills`.

If `to-spec` is not available, fall back to writing the spec yourself:
`docs/specs/YYYY-MM-DD-<topic>-design.md` (user preferences override this
default), then ask the user to review it before any implementation starts.
