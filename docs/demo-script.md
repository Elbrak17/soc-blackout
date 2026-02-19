# SOC Blackout — Demo Video Script (~3 minutes)

## Timing Breakdown

| Time | Section | Content |
|---|---|---|
| 0:00 - 0:30 | **HOOK** | The Problem + First Wow |
| 0:30 - 1:30 | **DEMO** | Full Agent in Action |
| 1:30 - 2:20 | **DEEP DIVE** | Architecture + Tools Used |
| 2:20 - 2:50 | **IMPACT** | Metrics + Differentiation |
| 2:50 - 3:00 | **CLOSE** | Call to Action |

---

## HOOK (0:00 - 0:30)

**Screen: Black screen with text overlay**

> "It's 3 AM. Your payment service just crashed. Average time to resolve? 45 minutes."

**Screen: Kibana dashboard showing metrics turning RED — CPU spike, error rate climbing**

> "Most SRE teams spend the first 15 minutes just figuring out WHAT happened. SOC Blackout knows in under 60 seconds."

**Screen: Agent Builder chat — type the question, agent starts responding immediately**

---

## DEMO (0:30 - 1:30)

**Scenario: OOM Crash**

**Screen: Agent Builder Chat**

Operator types: *"We're getting memory alerts on production. What's happening?"*

**Show the agent's full workflow:**

1. **DETECT** — Agent calls `anomaly_detector`: Shows metrics results (CPU, memory spikes)
   > "Watch how it automatically selects the right tool."

2. **DIAGNOSE** — Agent calls `log_analyzer`: Shows error patterns (OOMKilled across pods)
   > "47 error logs in the last 15 minutes. All pointing to memory exhaustion."

3. **CORRELATE** — Agent calls `incident_search`: Finds INC-001 from the knowledge base
   > "This is the killer feature — it searches 8 past incidents and finds the match. INC-001: same OOM pattern from last month's Black Friday surge."

4. **ASSESS** — Agent displays Confidence Score: 92%
   > "92% confidence. Above our 70% threshold. It's cleared to propose remediation."

5. **PROPOSE** — Agent presents structured recommendation
   > "Clear, structured output. The operator sees exactly what happened, why, and what to do."

**Operator types: "Go ahead, execute"**

6. **EXECUTE** — Agent triggers workflow, logs to audit trail
   > "Action logged. Post-mortem generated. Total time: under 2 minutes."

---

## DEEP DIVE (1:30 - 2:20)

**Screen: Architecture diagram (Mermaid — from docs/architecture.md)**

> "Here's how it works under the hood."

Highlight each component:
- **4 Custom Tools**: 2 ES|QL tools for real-time data, 1 Index Search for historical correlation, 1 Workflow for safe execution
- **Agent Builder**: Custom instructions define a strict 6-phase workflow
- **Safety Layer**: Confidence scoring, human approval gate, kill switch
- **MCP Server**: Same agent accessible from Slack, CLI, or IDE

**Screen: Show the agent instructions briefly**

> "The agent follows a strict protocol: Detect, Diagnose, Correlate, Assess, Propose, Execute. It never auto-executes without human approval."

**Screen: Show the ES|QL query briefly**

> "The ES|QL queries are parameterized — the agent can adjust time windows and thresholds dynamically."

---

## IMPACT (2:20 - 2:50)

**Screen: Before/After comparison**

| | Manual Triage | SOC Blackout |
|---|---|---|
| Time to diagnosis | ~15 min | < 30 sec |
| Time to find similar past incident | ~10 min | < 5 sec |
| Time to remediation | ~45 min | < 2 min |
| Audit trail | Manual documentation | Automatic |
| Post-mortem | Written next morning | Generated instantly |

> "From 45 minutes to under 2 minutes. That's not incremental improvement — that's a paradigm shift."

**Differentiation from other approaches:**

> "Unlike basic chatbots that just answer questions, SOC Blackout combines real-time data analysis with institutional memory. It learns from your past incidents and gets more accurate over time."

---

## CLOSE (2:50 - 3:00)

> "SOC Blackout. Built with Elastic Agent Builder. Open source on GitHub."

**Screen: GitHub repo link + social media tag**

> "Try it at [github link]. Built for the Elasticsearch Agent Builder Hackathon."

---

## Recording Notes

- **Resolution**: 1920x1080 minimum
- **Audio**: Clear voiceover, no background music during demo
- **Upload**: YouTube, set to Public
- **Captions**: Enable auto-captions
- **Length target**: 2:50 - 3:00 (judges stop watching at 3:00)
