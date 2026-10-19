---
title: "Study Copilot: Building an AI Agent That Acts on Connected Learning Data"
published: true
description: "A graph-grounded study assistant built with FalkorDB and FastAPI."
tags: ai, python, fastapi, database
---

# Study Copilot: Building an AI Agent That Acts on Connected Learning Data

## Why we built it

Students are surrounded by courses, articles, quizzes, and notes, but the difficult question is often simple: what should I do next? A flat resource list cannot reliably account for prerequisites, weak areas, progress, and available time. Study Copilot turns those connections into an explainable next action.

## The problem

A recommendation is only useful when it is relevant and actionable. Study Copilot retrieves a learner's graph context before deciding. It can recommend a topic, create a study plan, update progress, record a quiz attempt, mark a resource complete, and generate practice questions. State-changing actions require explicit confirmation.

## FalkorDB as the learning graph

The graph contains `User`, `Topic`, `Progress`, `SkillGap`, `Resource`, `Quiz`, `QuizAttempt`, `StudyPlan`, and `StudyPlanItem` nodes. Relationships include `HAS_PROGRESS`, `FOR_TOPIC`, `PREREQUISITE_OF`, `HAS_RESOURCE`, `HAS_QUIZ`, `TOOK`, `FOR_QUIZ`, `COMPLETED_RESOURCE`, and `CONTAINS`.

```cypher
MATCH (u:User {id:$user_id})-[:HAS_PROGRESS]->(p:Progress)-[:FOR_TOPIC]->(t:Topic)
MATCH (candidate:Topic)
WHERE candidate.estimated_minutes <= $minutes
  AND NOT EXISTS {
    MATCH (pre:Topic)-[:PREREQUISITE_OF]->(candidate)
    WHERE NOT EXISTS {
      MATCH (u)-[:HAS_PROGRESS]->(mp:Progress)-[:FOR_TOPIC]->(pre)
      WHERE mp.mastery >= 0.7
    }
  }
RETURN candidate
ORDER BY candidate.difficulty
```

This query makes prerequisite readiness a first-class part of the recommendation.

## Agent architecture

The browser calls FastAPI. The agent asks `StudyRepository` for user context and next topics, then creates a structured decision. `ActionService` stages mutations and executes them only after approval. The repository sends parameterized Cypher to FalkorDB. This keeps retrieval, decision logic, safety, and persistence separated without requiring an external LLM key for the demo.

## Feature walkthrough

1. Ask, `What should I study next?` to see a graph-grounded recommendation.
2. Ask, `Create a study plan`, then approve the pending action.
3. Ask, `Update my progress`, `Mark this resource complete`, and approve the mutation.
4. Ask, `Record a quiz attempt`, to stage the requested action.
5. Ask, `Generate practice questions` to retrieve the connected quiz for the recommended topic.

The UI exposes the retrieved context and action result so the user can see why the agent chose its recommendation.

## What we learned

Connected data changes the agent's role from answer generation to evidence-based decision making. FalkorDB makes prerequisite traversal and relationship inspection natural, while confirmation gates provide a practical safety boundary for actions that change learner records.

## Limitations and next steps

The demo uses deterministic intent routing and an in-memory pending-action store. Future work would add authenticated users, persistent audit events, richer question content, and an optional production LLM provider.
