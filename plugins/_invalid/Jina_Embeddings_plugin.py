
[0mΓûä
ΓûêΓûÇΓûÇΓûê ΓûêΓûÇΓûÇΓûê ΓûêΓûÇΓûÇΓûê ΓûêΓûÇΓûÇΓûä [0mΓûêΓûÇΓûÇΓûÇ ΓûêΓûÇΓûÇΓûê ΓûêΓûÇΓûÇΓûê ΓûêΓûÇΓûÇΓûê
ΓûêΓûæΓûæΓûê ΓûêΓûæΓûæΓûê ΓûêΓûÇΓûÇΓûÇ ΓûêΓûæΓûæΓûê [0mΓûêΓûæΓûæΓûæ ΓûêΓûæΓûæΓûê ΓûêΓûæΓûæΓûê ΓûêΓûÇΓûÇΓûÇ
ΓûÇΓûÇΓûÇΓûÇ ΓûêΓûÇΓûÇΓûÇ ΓûÇΓûÇΓûÇΓûÇ ΓûÇ  ΓûÇ [0mΓûÇΓûÇΓûÇΓûÇ ΓûÇΓûÇΓûÇΓûÇ ΓûÇΓûÇΓûÇΓûÇ ΓûÇΓûÇΓûÇΓûÇ

Commands:
  opencode acp                 Start ACP (Agent Client Protocol) server
  opencode [project]           start opencode tui                      [default]
  opencode attach <url>        attach to a running opencode server
  opencode run [message..]     run opencode with a message
  opencode auth                manage credentials
  opencode agent               manage agents
  opencode upgrade [target]    upgrade opencode to the latest or a specific
                               version
  opencode serve               starts a headless opencode server
  opencode web                 starts a headless opencode server
  opencode models              list all available models
  opencode stats               show token usage and cost statistics
  opencode export [sessionID]  export session data as JSON
  opencode import <file>       import session data from JSON file or URL
  opencode github              manage GitHub agent

Positionals:
  project  path to start opencode in                                    [string]

Options:
  -h, --help        show help                                          [boolean]
  -v, --version     show version number                                [boolean]
      --print-logs  print logs to stderr                               [boolean]
      --log-level   log level
                            [string] [choices: "DEBUG", "INFO", "WARN", "ERROR"]
  -m, --model       model to use in the format of provider/model        [string]
  -c, --continue    continue the last session                          [boolean]
  -s, --session     session id to continue                              [string]
  -p, --prompt      prompt to use                                       [string]
      --agent       agent to use                                        [string]
      --port        port to listen on                      [number] [default: 0]
      --hostname    hostname to listen on        [string] [default: "127.0.0.1"]
