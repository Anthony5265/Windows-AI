# Eco Computing

The Windows AI platform includes a lightweight :mod:`eco` package that helps
monitor and reduce energy consumption:

- **Energy tracking** – :class:`eco.tracker.EnergyTracker` reads battery and
  power information via OS APIs when available.
- **Off-peak scheduling** – :class:`eco.scheduler.EcoScheduler` can defer heavy
  compute tasks until configurable off‑peak hours.
- **Eco reports** – :func:`eco.reports.generate_report` summarizes the current
  power state and provides practical tips for reducing usage.

The Control Center integrates the scheduler, allowing prompts to be queued for
execution when the system is in an off‑peak window.
