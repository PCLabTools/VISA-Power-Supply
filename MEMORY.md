# Agent Memory

This file is a rolling memory for agents working on this project.
Use it to capture concise lessons from implementation feedback so similar future tasks can be handled better.

## Reusable Rules and Constraints

- Keep all module communication on Protocol; never use direct module-to-module calls.
- Keep power supply implementations behind a factory module to preserve a stable command contract.
- Every power supply implementation must support connect and disconnect.
- Preferred shared command surface across implementations: set_voltage, set_current, toggle_output, set_ovp, set_ocp, measure.
- Prioritize simulated implementation first, then add one to two real VISA models to validate scalability.
- Maintain a generic web UI served by a webserver module so higher-level projects can reuse the same front end.
