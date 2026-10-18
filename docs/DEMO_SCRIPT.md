# Study Copilot Demo Script

Target length: 2 minutes 30 seconds.

## 0:00-0:20 - Introduction

**On screen:** Open `http://localhost:8000`.

**Narration:** "Study Copilot is a graph-grounded learning assistant for choosing and acting on the next best study step. It uses FalkorDB to connect learners, progress, prerequisites, resources, and quizzes."

## 0:20-0:45 - Problem and Graph

**On screen:** Show the chat UI and context panel.

**Narration:** "Students often have resources but no clear order. The graph models prerequisite relationships, so a recommendation is based on connected learning evidence rather than a generic list."

## 0:45-1:15 - Recommendation

**On screen:** Enter `What should I study next?` and click Send.

**Narration:** "The agent retrieves the learner's progress and eligible topics from FalkorDB first. The context panel shows the graph records used, including the prerequisite-ready topic and resource."

## 1:15-1:55 - Action

**On screen:** Enter `Create a study plan`, click Send, then click Approve.

**Narration:** "A study plan changes graph state, so the agent stages it for explicit approval. After approval, the plan and topic items are created in FalkorDB and the result appears in the UI."

## 1:55-2:20 - More Actions

**On screen:** Try `Update my progress`, approve it, then try `Record a quiz attempt`.

**Narration:** "The same confirmation boundary protects progress and quiz records. Other supported actions include marking a resource complete and generating practice questions."

## 2:20-2:30 - Closing

**On screen:** Show the context and result panels.

**Narration:** "Study Copilot demonstrates how FalkorDB connected data can make an AI agent explainable and useful, while keeping state-changing actions under user control."
