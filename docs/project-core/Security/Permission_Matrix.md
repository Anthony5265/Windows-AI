# Permission Matrix
| Capability     | Default | Prompt | Notes                               |
|----------------|--------:|:------:|-------------------------------------|
| File read      | Allow   |  No    | Home directory only                 |
| File write     | Ask     |  Yes   | Home directory only                 |
| Shell run      | Ask     |  Yes   | Dangerous commands blocked          |
| Process list   | Allow   |  No    |                                     |
| Process kill   | Ask     |  Yes   | PID >= 100                          |
| Registry read  | Ask     |  Yes   |                                     |
| Registry write | Deny    |  Yes   | Require explicit allow in override  |
