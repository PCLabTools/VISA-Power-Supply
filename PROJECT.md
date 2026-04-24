# Project Mission

Build a reusable PAF-based VISA power supply platform that provides a generic web UI and a scalable factory module for multiple power supply models.

The project should enable both:
- Engineers who need a common remote front end for real lab power supplies.
- Developers who want to integrate a power supply module into other PAF automation projects.

## Problem Domain

Power supply control logic is often duplicated across projects and tied to specific instruments. This project defines a consistent command model and module architecture so new power supply models can be added without changing higher-level automation flows.

## Stakeholders and Users

- Lab and test engineers using a remote browser-based front end.
- Automation developers integrating power control into larger PAF systems.
- Future maintainers adding new VISA implementations.

## Goals and Success Criteria

Primary goals:
- Provide a generic browser UI served by a webserver module.
- Provide a factory-based VISA power supply module with simulated and real implementations.
- Keep module interfaces stable while adding new power supply models.

Success criteria:
- A simulated implementation is fully usable through the web UI.
- At least one to two real instruments can be added with no orchestration-level redesign.
- Common command interface remains consistent across implementations.

## Scope and Non-Goals

In scope for initial delivery:
- Simulated virtual power supply implementation.
- Webserver-hosted generic power supply UI.
- Factory-based power supply module architecture.
- Optional validation against one to two real-world supplies.

Out of scope for initial delivery:
- Vendor-specific UI screens for each model.
- Broad non-VISA protocol support (for example Modbus/CAN/LXI-only flows).
- Advanced lab resource scheduling and multi-user permissions.

## Functional Requirements

Required callable actions for all implementations:
- connect
- identity
- disconnect

Strongly expected actions for most implementations:
- set_voltage
- set_current
- toggle_output
- set_ovp
- set_ocp
- measure

Required workflows:
- User opens web UI and selects target power supply profile.
- System connects or disconnects from the selected device.
- User configures setpoints and protections.
- User toggles output on or off.
- UI and automation flows request measurements and receive latest telemetry.

## Non-Functional Requirements

Known expectations:
- Architecture must stay scalable and upgradeable as models are added.
- Module responsibilities should remain narrowly scoped.
- Inter-module communication must use Protocol messaging only.

Open non-functional items:
- Update rate and latency targets for measurement refresh.
- Error handling and retry policy for VISA communication failures.
- Safety behavior on disconnect, timeout, or process shutdown.
- Deployment target details (single host, container, service wrapper).

## Architecture Intent (PAF)

All features are Module subclasses communicating over Protocol.

Rules:
- No direct module-to-module calls.
- Power supply model differences are isolated in factory implementations.
- UI-facing workflows go through orchestration commands, not implementation-specific calls.

## Candidate Module Breakdown

### Core Runtime Modules

1. PowerSupplyOrchestrator (address: power_supply_orchestrator)
- Responsibility: Coordinate user and automation requests into stable power-supply workflows.
- Inbound commands: initialize_session, connect, disconnect, set_voltage, set_current, toggle_output, set_ovp, set_ocp, measure, get_status.
- Outbound messages/requests: send_request to visa_power_supply for command execution; send_action to telemetry_state and event_logger.
- Owned state: selected device profile, connection status, last command results, active limits.
- Dependencies: visa_power_supply, telemetry_state, event_logger.

2. TelemetryState (address: telemetry_state)
- Responsibility: Maintain latest readbacks and derived status for UI and automation.
- Inbound commands: update_measurement, get_latest, clear_state.
- Outbound messages/requests: send_response to requesters; optional event publication to health_monitor.
- Owned state: latest voltage/current/power readings, timestamp, output state snapshot.
- Dependencies: health_monitor (optional), web_ui_server (read path only via protocol request).

### Integration Modules

1. VisaPowerSupplyFactory (address: visa_power_supply)
- Responsibility: Factory module exposing a stable command contract while selecting implementation_type.
- Inbound commands: connect, disconnect, set_voltage, set_current, toggle_output, set_ovp, set_ocp, measure, identify.
- Outbound messages/requests: responses to caller; optional diagnostic events to event_logger.
- Owned state: implementation_type, transport/session handles, instrument capability map.
- Dependencies: VISA stack and implementation classes only.

Planned implementations:
- SimulatedVisaPowerSupply: deterministic virtual device for development and tests.
- Real device implementations (candidate examples): RigolDp8xxVisaPowerSupply, KeysightE36xxVisaPowerSupply.

2. WebUiServer (address: web_ui_server)
- Responsibility: Serve generic power supply UI and map user actions to orchestrator commands.
- Inbound commands: start_server, stop_server, ui_action, get_ui_state.
- Outbound messages/requests: send_request to power_supply_orchestrator and telemetry_state.
- Owned state: server bind config, session map, active UI clients.
- Dependencies: HTTP/web framework and static assets.

### Support Modules

1. EventLogger (address: event_logger)
- Responsibility: Centralized structured event and command logging.
- Inbound commands: log_event, log_error, flush.
- Outbound messages/requests: optional alerts to health_monitor.
- Owned state: buffered log entries, sink configuration.
- Dependencies: file or console sink.

2. HealthMonitor (address: health_monitor)
- Responsibility: Monitor module liveness and integration health.
- Inbound commands: heartbeat, report_fault, get_health.
- Outbound messages/requests: alert actions to main and event_logger.
- Owned state: per-module health status, recent faults, heartbeat timestamps.
- Dependencies: protocol-visible module addresses only.

## Risks, Assumptions, Open Questions

Assumptions:
- VISA is the primary hardware integration path for this project phase.
- A shared generic UI is preferred over model-specific pages.

Risks:
- Command behavior differences across vendors may pressure the common interface.
- Safety defaults may differ between simulated and real instruments.
- VISA driver/environment setup can vary by host machine.

Open questions:
- Which exact real instruments are targeted first?
- What measurement polling cadence is required for acceptable UX?
- What is the required behavior on communication timeout during output-enabled operation?
- Should authentication be required for web UI in initial phase?

## Initial Delivery Plan

Phase 1:
- Implement VisaPowerSupplyFactory with SimulatedVisaPowerSupply.
- Implement PowerSupplyOrchestrator and TelemetryState baseline.
- Implement WebUiServer with generic single-supply control view.

Phase 2:
- Add first real VISA implementation and validate command parity.
- Add structured logging and health monitoring support modules.
- Add integration and module-level tests for connect/control/measure workflows.

Phase 3:
- Add second real implementation to validate extensibility.
- Harden timeout/retry/safety behaviors and finalize acceptance criteria.
