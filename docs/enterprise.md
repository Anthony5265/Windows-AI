# Enterprise Deployment

The Windows AI Control Center supports enterprise deployments through a set of
features aimed at teams and regulated environments.

## Multi-User Sessions
- The backend layer now includes a session manager that isolates user
  conversations and maintains history per session.

## Shared Dashboards
- Administrators can create dashboards and share them with team members.
- Role-based access control limits each user's abilities to **view** or **edit**
  shared dashboards.

## Single Sign-On
- Integration with Microsoft Entra ID using the MSAL library.
- Supports device code and interactive flows for seamless authentication.

## Policy Management
- ADMX templates define egress, telemetry, and update restrictions.
- Policies can be loaded and queried through the `PolicyManager` module.

## Compliance Logging
- Security events and permission changes are logged for auditing.
- Compliance events can be exported in JSON or CSV for external reporting.

These capabilities enable centralized control while satisfying common
enterprise requirements.
