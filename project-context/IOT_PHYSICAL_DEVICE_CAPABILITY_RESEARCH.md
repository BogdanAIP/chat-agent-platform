# IoT / Physical Device Capability Family — Stage Research Brief

Status: **STAGE RESEARCH BRIEF — DEFER PRODUCTION ADOPTION**

Research date: 2026-08-28

Project snapshot: `BogdanAIP/chat-agent-platform@adc1aa3206fe3b3cf2b08bd963b29ed482609dba`

<!-- IOT_PHYSICAL_DEVICE_DECISION_V1
stage_decision=DEFER
production_iot=BLOCKED
future_capability_family=RESEARCH_SELECTED
first_backend_candidate=HOME_ASSISTANT
mhs_dependency=REFERENCE_ONLY
critical_path_change=NO
-->

## Decision authority

The structured `IOT_PHYSICAL_DEVICE_DECISION_V1` block above is the sole implementation-decision representation in this Brief.

Production IoT/device-control work is **blocked** by this Brief. It does not authorize a new Chat-facing tool, Home Assistant dependency, device mutation path, Matter/MQTT direct adapter, scheduler, automation engine, hardware driver or physical safety controller.

The research does establish one durable future direction:

- **Physical Device / IoT** is a credible future capability family below the existing project Control Plane;
- **Home Assistant is the preferred first backend candidate for future re-entry**, not an accepted production dependency;
- direct Matter, direct MQTT and vendor-specific adapters are **measured-gap-only** alternatives rather than default parallel stacks;
- MHS is a **reference-only architecture signal** while its public specification/implementation remains incomplete for independent adoption research;
- Stage 26.3C and the current release-critical sequence do not change.

A future implementation requires fresh Stage Research on then-current Home Assistant/code/protocol versions, a concrete user/device scope, security/identity/recovery semantics and target physical acceptance.

---

## Stage goal

Define whether the existing project architecture can extend coherently from computer-use to physical devices without turning the Chat-facing surface into hundreds of vendor/device tools and without delegating project authority or verification to a home-automation hub.

Target conceptual shape:

```text
ordinary ChatGPT
        |
        v
project semantic capability / procedure
        |
        v
Control Plane
  authorization / scope / consequence policy
  WorkingState / reconciliation / LoopGuard
  ExpectedEffect / Verification Kernel / Finish Gate
        |
        v
future Physical Device / IoT adapter family
        |
        +--> Home Assistant candidate
        |      +--> Matter
        |      +--> MQTT
        |      +--> Zigbee / Z-Wave / Bluetooth
        |      +--> vendor/native integrations
        |
        +--> direct protocol/vendor adapters only for measured gaps
        |
        +--> future MHS/laboratory adapter after separate public-spec research
```

The project should reason in stable semantic consequences such as `turn light off`, `set climate target`, `close cover`, `run qualified home procedure`, not generic `call_service(anything)` or hundreds of vendor commands.

---

## Current project baseline

### Release order

The release-critical path remains Stage 26.3C production WorkingState/restart-reconciliation integration, followed by the existing broad computer-use/OpenAdapt/26.4/26.5/release sequence. This research is future/non-release-critical and must not displace that order.

### Existing common mechanics already fit the problem

The project already owns:

```text
Capability / Subject identity
ObservationSnapshot + provenance + freshness
ExpectedEffect
PASS | FAIL | UNKNOWN
WorkingState
AttemptIntent / AttemptRecord
fresh reconciliation before unsafe retry
LoopGuard / budgets
independent Finish Gate
procedure_run
```

Those are deliberately capability-spanning. Physical devices therefore do **not** justify a second control plane or a second completion authority.

### No prior IoT normalization role exists in the reuse baseline

`ARCHITECTURE_REUSE_BASELINE.md` has no existing role for smart-home/IoT device normalization/execution. The role is therefore **new architecture** under the Stage Research Scope Expansion Gate.

Adjacent project-owned roles remain unchanged:

| Affected role | Prior owner | IoT result | Lineage decision |
|---|---|---|---|
| General planning / novel strategy | ordinary ChatGPT | still proposes goals/strategy; not a real-time safety controller | `KEEP` |
| Capability authorization / consequence policy | project Control Plane | device/backend output cannot grant itself authority | `KEEP` |
| Capability-spanning operational state | project WorkingState | project operation/recovery history remains above the hub | `KEEP` |
| Transition verification authority | project Verification Kernel | hub/service success is evidence, never project `PASS` | `KEEP` |
| Task completion authority | project Finish Gate | device/backend completion is not project `DONE` | `KEEP` |
| Procedure compiler / deterministic execution | OpenAdapt/project `procedure_run` lineage | remains the selected general procedure seam; HA scripts may be backend mechanics only if future research proves fit | `KEEP` |
| Physical device / IoT normalization + bounded execution | no prior baseline role | new role; Home Assistant is strongest first candidate in this research | `DEFER` production / preferred first candidate |
| MHS/laboratory hardware semantic standard | no prior baseline role | public research-preview signal only; no production dependency selected | `DEFER` / `REFERENCE_ONLY` |

No accepted project-owned authority role is replaced.

---

## Architecture primitives and engineering domains

A future Physical Device capability would materially rely on these mechanisms. The Brief chooses only the capability boundary and candidate ordering; it does not preselect unresearched recovery/concurrency primitives.

| Primitive / concern | Engineering domain | Required property here | Current decision |
|---|---|---|---|
| device/entity identity | device registry / identity lifecycle | survive rename/reload/restart without confusing subjects | research contract required |
| command vs observed state | control systems / device integration | delivery is distinct from physical effect | must preserve |
| event/state freshness | event-driven systems / observation consistency | stale/delayed/replayed state cannot prove a new effect | must preserve |
| consequence authorization | capability security / safety | backend cannot broaden project scope | project-owned `KEEP` |
| ambiguous delivery | distributed systems / idempotency / reconciliation | no blind retry after unknown physical outcome | mechanism unresolved; fresh research required |
| resource ownership | concurrency / physical resource arbitration | mutually exclusive hardware resources cannot collide | future research only when concrete multi-device consumer exists |
| safety interlocks | industrial/control safety | hazardous effects remain below LLM authority | mandatory boundary; exact implementation device-specific |
| procedure promotion | program synthesis / workflow validation | successful adaptive traces are not automatically trusted automation | future research seam |

Do not infer a concrete lock/ledger/idempotency-key implementation merely from the requirement to avoid duplicate physical effects. Any such mechanism is itself subject to fresh solution-domain research.

---

## Problem evidence

### P1 — vendor-by-vendor integration does not scale as the default architecture

A future device family can easily span lights, locks, covers, climate, media, sensors, relays and many vendor transports. Exposing each vendor SDK/API directly would create a large unstable backend and public-tool surface while duplicating mature integration work.

The current Module Selection Policy already prefers official/local runtimes and mature focused adapters before custom integrations, and explicitly says a new backend should normally not create another ChatGPT app/plugin or raw generic tool catalog.

### P2 — physical action success and physical effect are different facts

A service/API call may finish while the target device has not changed, may change later, may be offline, may expose an assumed state, or may produce an effect whose acknowledgement is lost.

Therefore physical actions require:

```text
fresh pre-observation
 -> authorize bounded action
 -> deliver action
 -> fresh post-action observation
 -> verify ExpectedEffect
 -> PASS | FAIL | UNKNOWN
```

Service/API completion alone is never sufficient for project `PASS`.

### P3 — identity is richer than a human-friendly entity name

User-facing names such as `light.living_room` are routing aliases and may be renamed. A physical capability needs stronger subject identity/provenance so WorkingState and recovery cannot silently bind a new device/entity to an old operation.

### P4 — physical consequences require a risk gradient

Turning off a lamp and unlocking an exterior door are not equivalent consequences. The platform needs capability-specific consequence policy, freshness and interlock requirements rather than one generic device-call permission.

This research deliberately does **not** freeze a universal numeric risk taxonomy. It establishes the boundary:

```text
low-consequence comfort action
  -> bounded project authorization + fresh verification

higher-consequence actuator
  -> stronger scope/freshness/preconditions

safety-critical / hazardous equipment
  -> qualified deterministic procedure + external/device interlocks
  -> LLM is never the final safety authority
```

### P5 — adaptive exploration should not remain forever in the hot path

The supplied MHS research-preview material describes a useful long-horizon pattern: adaptive experimentation can converge on a validated deterministic procedure that later runs without an LLM on every step. This aligns with the project's existing `procedure_run`, candidate-skill and deterministic-execution direction, but it does not yet select a procedure-synthesis mechanism.

---

## Solution evidence

## Source-code evidence

### Home Assistant Core — stable 2026.8.2

Repository/ref: `home-assistant/core@3fb456fa1fe4abbe6b89367b98f282043e9b02dd` (`2026.8.2`)

Classification: `OPEN_IMPLEMENTED` for the state/service/registry mechanics inspected here.

Lesson: `REUSE_COMPONENT` candidate behind a project-owned adapter, pending future security/recovery/physical qualification.

Inspected paths:

- `homeassistant/components/websocket_api/commands.py`
- `homeassistant/helpers/entity_registry.py`
- `homeassistant/helpers/device_registry.py`
- `homeassistant/helpers/entity.py`
- `homeassistant/helpers/service.py`
- `tests/components/websocket_api/test_commands.py`

#### Command/state path

`handle_call_service(...)` accepts a WebSocket service request and awaits `hass.services.async_call(..., blocking=True, ...)`, then returns a result/context to the client. Separately, the WebSocket API exposes `get_states` and `subscribe_events`; `state_changed` subscriptions are permission-filtered.

This proves an important boundary:

```text
HA service handler completed
!=
project ExpectedEffect proven
```

The future adapter must use service completion as delivery/execution evidence and obtain a fresh post-action state/event observation before project verification.

#### Identity path

`RegistryEntry` contains `entity_id`, `unique_id`, `platform`, `config_entry_id`, `device_id` and a generated registry `id`. Device registry entries use integration-scoped identifiers/connections and explicitly detect identifier/connection collisions.

Project implication: `entity_id` alone must not be the durable subject identity. A future `SubjectRef` should bind an HA instance plus stable registry/integration/device identity, keeping `entity_id` as a current routing/display alias. Exact field composition remains an implementation research question because registry semantics may evolve.

#### Observation quality

The `Entity` base exposes `available` and `assumed_state`; `assumed_state` explicitly means Home Assistant is unable to access the real state of the entity.

Project implication: an observation that is unavailable/unknown/assumed may be insufficient for a high-confidence physical `PASS`, depending on the capability's required evidence strength.

#### Permissions

Home Assistant has user/context permission checks, including admin-only services and entity-control checks in entity-service resolution paths. These are valuable defense-in-depth but do not replace project consequence policy. The future adapter must not assume that possession of an HA credential makes every HA service semantically authorized by Chat Agent Platform.

#### Negative space / unresolved points

This research does not prove:

- exactly-once device effects across HA/device/network restart;
- that all integrations expose equally strong state freshness;
- a durable project operation identity in HA request IDs/contexts;
- that an HA service result proves real-world state;
- one universal permission model for all integrations/services;
- safe rollback for arbitrary actuators.

Those remain explicit re-entry research/acceptance topics.

### openHAB Core — independent aggregator reference

Repository/ref: `openhab/openhab-core@4bb2ebf810ba84563c9f3ebc04b0443218444ab2`

Classification: `OPEN_PARTIAL` for the broader adapter role; `OPEN_IMPLEMENTED` for the command-versus-state separation inspected here.

Lesson: `REFERENCE_ONLY` / viable independent aggregator alternative.

Inspected path:

- `bundles/org.openhab.core/src/main/java/org/openhab/core/items/GenericItem.java`

`internalSend(...)` publishes a command event. State application/update is a separate path that notifies listeners and publishes state-updated/state-changed events.

Independent project lesson: the desired project contract is not a Home Assistant quirk. Mature home-automation runtimes also separate **command intent/delivery** from **observed state**.

This research did not trace enough of openHAB's current auth/REST/device-identity/recovery stack to claim full parity with the required Chat Agent Platform adapter role; therefore it remains an independent comparison/reference rather than a selected dependency.

### Anthropic Model Hardware Standard (MHS)

Public source/spec status at research date: research preview announced 2026-08-27; public materials describe a model-agnostic hardware abstraction for devices, states, procedures and safety limits, with planned broader/open availability. The complete implementation/specification required for independent production adoption was not available in this research.

Classification: `DOCUMENTED_ONLY` / `OPEN_PARTIAL` for the product concepts relevant here.

Lesson: `REFERENCE_ONLY`.

Useful architecture lessons:

- physical-device abstraction should expose state/capabilities/constraints/procedures rather than raw vendor APIs;
- closed-loop `observe -> act -> re-observe -> verify` is central;
- camera/pixel evidence may support concrete physical preconditions but is not self-authorizing;
- deterministic machine-level safety checks remain below the model;
- adaptive work can be converted to validated deterministic procedures;
- fast/real-time device loops should run locally/deterministically rather than asking an LLM on every control cycle.

Do not add an MHS dependency or compatibility claim until its public specification/implementation can be revalidated directly.

---

## Protocol/backend evidence

### Matter through Home Assistant

Current Home Assistant documentation describes the Matter integration as local control over Wi-Fi/Thread and as a controller connected to a separate Matter Server process through WebSocket. Matter is therefore already reachable through a mature local normalization layer without writing a project Matter controller today.

Important limitation: native Home Assistant integrations can expose capabilities that Matter bridges do not. Direct Matter is not automatically a richer or simpler project path.

### MQTT through Home Assistant

Current Home Assistant MQTT integration supports discovery/manual configuration across many entity types. MQTT itself has delivery/retained-message/staleness semantics that require careful observation and reconciliation; the HA documentation explicitly notes that a retained value may replay an older state and that missed updates can delay freshness.

Project implication: direct MQTT is not “free”. It would introduce its own identity, topic schema, QoS/retained-state, discovery and reconciliation surface. Prefer HA first unless a measured requirement needs direct protocol access.

---

## Alternatives comparison

| Approach | State/normalization owner | Strengths | Main risks/gaps | Current disposition |
|---|---|---|---|---|
| A. no IoT capability family | none | zero scope/risk now | foregoes a coherent future physical-device path | `KEEP current production`; future family may remain deferred |
| B. Home Assistant behind narrow project adapter | HA normalizes devices/entities; project owns authority/verification | broad mature integrations, local state/events/services, registry identity, Matter/MQTT reach | backend semantics vary; service completion != effect; permission/recovery qualification required | **preferred first future candidate; production `DEFER`** |
| C. openHAB behind narrow project adapter | openHAB items/things/event bus | independent mature aggregator; command/state split | less code investigated for our exact auth/identity/recovery fit | viable alternative/reference; `DEFER` |
| D. direct Matter + direct MQTT project adapters | project/protocol stack | lower-level control, possibly protocol-specific features/latency | duplicate integration burden, more identity/recovery/security surfaces | **measured-gap-only `DEFER`** |
| E. vendor-specific adapters by default | project/vendor APIs | can expose vendor-specific features | unbounded maintenance/tool surface and duplicated ecosystem work | `REJECT` as default architecture strategy; allow only measured exceptions |
| F. wait for MHS and adopt it directly | MHS | promising hardware semantics | research preview; incomplete public adoption evidence | `DEFER` / `REFERENCE_ONLY` |

### Why Home Assistant leads without becoming authority

Home Assistant currently has the strongest fit because it already combines:

```text
stable entity/device registries
+ state/event observation
+ bounded service/action execution
+ broad local/vendor integration ecosystem
+ Matter/MQTT access
```

while allowing the project to keep:

```text
user intent / planning
+ consequence policy
+ durable operation identity
+ WorkingState / recovery
+ ExpectedEffect / Verification Kernel
+ independent Finish Gate
```

That is the intended reuse seam.

---

## Proposed future adapter contract — conceptual only

This is a research boundary, not an implementation schema.

### Observation

A future HA-backed observation should be able to bind at least:

```text
HA instance identity
stable registry/integration/device subject identity
current entity routing alias
state + relevant attributes
availability / unknown / unavailable state
assumed-state signal where exposed
observation/event time + project freshness evidence
source/integration/provenance
```

### Action

Do **not** expose a generic public `ha.call_service(anything)` capability.

Prefer project semantic operations/procedures such as:

```text
TurnOffLight
SetClimateTarget
CloseCover
LockDoor
RunQualifiedHomeProcedure
```

or an equivalent bounded internal schema selected by future implementation research.

The project authorizes the semantic effect and maps it to an HA backend action. The backend cannot reinterpret a narrow grant as generic service authority.

### Verification

```text
fresh pre-state
 -> authorize
 -> backend action delivery
 -> fresh state/event/sensor evidence
 -> project ExpectedEffect verification
 -> PASS | FAIL | UNKNOWN
```

If the backend reports success but fresh evidence contradicts the expected physical result, project verification returns `FAIL` or `UNKNOWN` as appropriate.

---

## Consequence and safety boundary

Exact risk classes are deliberately not frozen yet. The durable rule is consequence-sensitive authority.

Representative progression:

```text
read-only sensor
 -> observation permission

light / media / ordinary cover
 -> bounded action + fresh verification

climate / outlet / powered appliance
 -> bounded ranges + policy/preconditions

lock / gate / alarm
 -> stronger scope, freshness and explicit authorization

water / boiler / pump / high-energy actuator
 -> qualified procedure + device/environment interlocks

hazardous gas / laboratory / safety-critical machinery
 -> independent hardware/process safety interlocks
 -> LLM cannot be final safety authority
```

Home Assistant, MHS or any other backend may expose its own safety/permission features, but those are subordinate evidence/defense-in-depth, not replacements for project policy.

---

## Failure / Crash Matrix for future re-entry

| Failure boundary | Possible physical state | Required project behavior |
|---|---|---|
| HA unavailable before action | unchanged | capability unavailable; no fallback mutation |
| auth/token revoked or scope insufficient | unchanged | fail closed; never broaden credential/scope automatically |
| target entity/device unknown/unavailable | unknown/unchanged | no unsafe mutation; require fresh identity/state |
| state is assumed rather than observed | may differ from HA state | evidence strength depends on consequence; high-risk `PASS` requires stronger evidence |
| request rejected before HA service execution | unchanged | `CONFIRMED_NOT_APPLIED` only with sufficient evidence |
| service handler completes but device does not change | unchanged | fresh re-observation -> `FAIL`/`UNKNOWN`; handler result is not `PASS` |
| device changes after delayed integration update | changed, HA stale | wait/reobserve within bounded policy; do not immediately duplicate action |
| device changes but action response/connection is lost | changed possible | WorkingState marks ambiguous outcome; fresh reconciliation before any retry |
| WebSocket disconnect after delivery | changed or unchanged | request id is not enough; reconnect + fresh observation/reconciliation |
| HA restarts during action | changed or unchanged | no blind redelivery; rebind identity and reobserve |
| duplicate/replayed project delivery | duplicate effect possible | observable requirement: no additional unsafe effect before reconciliation; concrete idempotency primitive requires separate research |
| entity renamed | same device/entity | stable registry/integration identity must prevent subject replacement |
| integration/config entry reloaded/replaced | same/new device ambiguous | revalidate subject provenance before mutation |
| physical user changes device out-of-band | state diverges from prior plan | fresh state wins; stale WorkingState cannot authorize mutation |
| HA automation/scene causes secondary effects | multiple devices may change | only qualified/expected effect scope may count; unexpected effects become evidence/failure |
| Matter Server unavailable | Matter device state/actions unavailable | capability unavailable; no silent vendor-cloud fallback |
| Matter node unreachable | unchanged/unknown | bounded failure; no blind retry for high-consequence action |
| MQTT retained message replays old state | stale apparent state | freshness/provenance required; retained payload alone cannot prove new effect |
| MQTT update lost/delayed | physical state unknown | `UNKNOWN` until fresh evidence or bounded timeout policy |
| required safety interlock unavailable | hazardous | action blocked regardless of planner request |
| backend/sensor evidence conflicts | unknown physical truth | `UNKNOWN`; zero unauthorized continuation |
| rollback/compensation is unsafe or prior outcome unresolved | unknown | no automatic compensation until separate verified policy permits it |

No row selects an exactly-once, lock, transaction, queue or durable-dedup implementation. Those mechanisms require their own research if a future consumer needs them.

---

## Experience -> validated deterministic procedure seam

The IoT/MHS evidence strengthens a future research direction already compatible with project procedures:

```text
adaptive attempts
 -> verified successful traces
 -> candidate procedure
 -> independent validation
 -> bounded deterministic procedure
 -> versioned procedure / skill lineage
```

This is **not** automatic self-modification and not part of this production decision.

Rules for future research:

- a successful trace is evidence, not automatically trusted code;
- candidate synthesis must preserve declared inputs, constraints, ExpectedEffects and resource/safety requirements;
- promotion requires replay/regression/variant testing and independent verification;
- high-risk device procedures require separate physical qualification and interlocks;
- once qualified, the deterministic procedure should remove the LLM from timing-sensitive inner loops where possible;
- a failed/stale procedure must escalate back to the planner instead of improvising beyond its grant.

MHS is useful external problem/architecture evidence for this seam, but does not currently provide an adopted project synthesis runtime.

---

## Re-entry triggers

Run fresh Stage Research before any production IoT/device-control implementation when at least one concrete consumer exists, for example:

1. a real user wants bounded smart-home control through the platform;
2. a laboratory/device integration needs the same state/action/verification model;
3. a physical-device task exposes a measured gap in Home Assistant that may justify direct Matter/MQTT/vendor access;
4. a qualified procedure needs resource arbitration/leases across multiple physical devices;
5. Home Assistant/MHS/openHAB architecture materially changes;
6. high-consequence devices require a formal interlock/authorization model;
7. repeated verified adaptive traces justify research into procedure synthesis/promotion.

At re-entry:

- pin current upstream versions again;
- define the exact supported device/consequence classes;
- inspect current source/tests/failure history;
- research any new recovery/idempotency/resource-lock/interlock primitive directly;
- decide the public semantic surface truthfully;
- prove target physical behavior rather than relying on mocks/backend success.

---

## Acceptance ladder for a future bounded Home Assistant spike

If a future Brief returns `PROCEED`/`NARROW`, minimum evidence should include:

### L1 — adapter/contract

- stable identity mapping survives entity rename;
- read-only state/event observation with freshness/provenance;
- `available` / unknown / assumed-state handling;
- bounded semantic action -> exact HA backend mapping;
- generic raw service dispatch is not Chat-facing authority;
- HA action result cannot directly create project `PASS`/`DONE`;
- credential/permission negative tests;
- ambiguous outcome blocks unsafe retry.

### L2 — multi-device workflow

- representative light/switch/climate/cover family;
- device unavailable/reconnect/reload variants;
- delayed state update and lost response fault injection;
- one qualified deterministic home procedure;
- project WorkingState/reconciliation survives local process restart without blind duplicate consequence.

### L3 — ordinary user physical task

Example bounded user goal:

```text
"I'm leaving home; turn off allowed lights/media and set the permitted climate away target."
```

The gate must independently prove:

- correct physical subjects were selected;
- only authorized consequence classes changed;
- fresh post-action state/evidence supports each required ExpectedEffect;
- unresolved/unavailable devices are reported rather than guessed;
- no unauthorized lock/alarm/high-risk action occurred;
- Finish Gate uses fresh final evidence, not planner/backend self-report.

Higher-risk device classes require their own physical acceptance and safety/interlock evidence; a successful lamp demo does not authorize door locks, water, boilers, gas or laboratory actuators.

---

## Final conclusion

The project's current architecture does not need to be redesigned for IoT. The same high-level consequence model can extend beyond Browser/Windows when backend-specific observation/action mechanics remain below project-owned authority:

```text
identify
 -> observe
 -> authorize
 -> act
 -> fresh re-observe
 -> verify
 -> reconcile/recover
 -> optionally promote verified experience into a separately validated procedure
```

**Top-level decision: `DEFER` production IoT work.**

**Future architecture direction: define a Physical Device / IoT capability family.**

**Preferred first backend candidate on future re-entry: Home Assistant**, because current source evidence shows the state/event/service/registry separation needed for a narrow adapter and it already aggregates broad local/protocol/vendor integrations.

**Direct Matter/MQTT/vendor adapters remain measured-gap-only.**

**MHS remains reference-only until its public specification/implementation can be independently researched.**

Nothing in this Brief changes Stage 26.3C, the six current public tools, current runtime authority or release order.
