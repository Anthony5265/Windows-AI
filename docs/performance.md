# Performance Profiles and Auto-Tuning

The Windows AI platform includes lightweight helpers to inspect system
performance and suggest optimizations.

- **Metrics collection** – :class:`performance.optimizer.SystemOptimizer`
  gathers CPU, memory and disk statistics using ``psutil`` when available.
- **Profiles** – :func:`performance.optimizer.SystemOptimizer.collect_metrics`
  returns a snapshot of the current hardware and OS state.
- **Auto-tuning** – :func:`performance.optimizer.SystemOptimizer.recommend_tweaks`
  analyzes the metrics and produces simple recommendations.
- **Dashboard** – :class:`control_center.performance_gui.PerformanceGUI` presents
  live readings and tips in a small Tkinter window.

These tools help users keep their systems responsive by identifying bottlenecks
and offering actionable suggestions for tuning.
