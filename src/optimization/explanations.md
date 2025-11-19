# Optimization Profiles

The optimization module provides three hardware tuning profiles:

- **balanced** – default settings for everyday workloads.
- **performance** – maximizes speed at the cost of extra power usage.
- **eco** – reduces performance for better battery life.

Each profile adjusts CPU and GPU tuning parameters. The module keeps track of
previous settings so users can call `revert()` to return to the earlier
configuration.
