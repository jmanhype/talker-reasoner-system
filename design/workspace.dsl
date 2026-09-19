workspace "Talker Reasoner System" "A staged fast/slow voice agent with calibrated routing, governed proposals, audited state, and policy-gated tool execution." {

  model {
    operator = person "Operator" "The single authorized human using and administering the prototype."

    trs = softwareSystem "Talker Reasoner System" "Routes voice turns, governs model proposals, renders safe responses, and stages state, audit, and tool execution." {
      voiceEdge = container "Voice Edge" "Browser and WebSocket audio/session edge; coordinates typed and spoken input, one-stream audio arbitration, interruption, accessibility channels, and turn epochs without reasoning or execution authority." "TypeScript"
      routing = container "Routing Service" "Applies versioned calibration, threshold, and fail-closed policy to an ephemeral transcript." "Python"
      reasoning = container "Reasoner Coordinator" "Owns asynchronous reasoner jobs and binds one typed proposal to its request, catalog, policy, and turn epoch." "Python"
      actionGovernor = container "Action Governor" "Validates action schemas and scopes, applies fail-closed policy preflight, and manages exact confirmations." "Python"
      toolCatalog = container "Tool Catalog" "Versioned reviewed allowlist of canonical tool schemas, permissions, risks, scopes, bounds, and provenance." "Python and PostgreSQL"
      toolGateway = container "Tool Gateway" "The sole executor boundary for allowlisted, policy-authorized actions; filters results and isolates credentials." "Python"
      renderer = container "Response Renderer" "Builds bounded policy-safe text and audio responses with priority, cancellation, and channel rules." "TypeScript/Python"
      eventLedger = container "Event Ledger" "Append-only scoped-hash event chain and integrity verifier for minimized audit evidence." "Python and PostgreSQL"
      hotState = container "Hot State" "TTL-bound minimized session snapshot for the live voice loop." "Redis" "Database"
      memoryGovernor = container "Memory Governor" "Later consent-gated semantic memory broker with provenance, review, recall, supersession, and deletion." "Python"
      observability = container "Observability" "Versioned metrics, alerts, traces, privacy canaries, and replay evidence without raw content." "Python"
    }

    personaplex = softwareSystem "PersonaPlex" "Real-time full-duplex speech-to-speech talker." "External"
    voxtral = softwareSystem "Voxtral Realtime" "Streaming speech transcription service." "External"
    jev = softwareSystem "Jev" "Calibrated ultra-fast routing and reranking service." "External"
    reasoner = softwareSystem "Direct Reasoner" "One direct tool-calling model or local scripted transport that proposes but never executes." "External"
    magg = softwareSystem "MAGG" "Meta-MCP aggregator with separate admin and runtime surfaces." "External"
    contextForge = softwareSystem "Context Forge" "MCP and REST federation gateway; deferred until redeployed and health-checked." "External"
    dagger = softwareSystem "Dagger" "Container-native deterministic CI/CD execution backend; deferred behind policy." "External"
    treg = softwareSystem "Treg" "External tool catalog, credential proxy, and billing boundary; deferred behind budget gates." "External"
    localMcp = softwareSystem "Local MCP Tool" "One allowlisted local read-only MCP capability." "External"
    postgres = softwareSystem "PostgreSQL" "Durable append-only events and catalog records." "External"
    redis = softwareSystem "Redis" "Hot-state backend." "External"
    memoryPlatform = softwareSystem "Memory Platform" "Deferred Mem0, Cognee, Zep, or Letta memory backend." "External"
    tts = softwareSystem "Clean TTS" "Separate clean speech renderer for slow-path responses." "External"

    operator -> voiceEdge "Speaks or types" "WSS/HTTPS"
    operator -> toolCatalog "Administers catalog versions" "Admin UI/API"
    operator -> magg "Administers servers and kits through admin plane only" "MAGG admin"

    voiceEdge -> personaplex "Streams full-duplex audio" "WSS"
    voiceEdge -> voxtral "Streams transcription audio" "WSS/HTTP"
    voiceEdge -> routing "Submits normalized ephemeral transcript" "in-process/HTTP"
    voiceEdge -> hotState "Reads/writes bounded turn snapshot" "Redis protocol"
    voiceEdge -> renderer "Requests fast or slow presentation" "in-process/HTTP"
    voiceEdge -> tts "Renders clean slow answer" "HTTP"

    routing -> jev "Requests calibrated labels" "HTTPS"
    routing -> reasoning "Creates asynchronous slow job" "in-process/HTTP"
    routing -> eventLedger "Appends route evidence" "in-process/HTTP"

    reasoning -> reasoner "Requests one typed proposal" "HTTPS/local"
    reasoning -> actionGovernor "Submits proposals for validation and policy" "in-process/HTTP"
    reasoning -> eventLedger "Appends job and proposal evidence" "in-process/HTTP"

    actionGovernor -> toolCatalog "Loads exact catalog and policy version" "in-process/SQL"
    actionGovernor -> toolGateway "Dispatches only authorized action" "in-process/HTTP"
    actionGovernor -> eventLedger "Appends validation, policy, and confirmation evidence" "in-process/HTTP"

    toolGateway -> magg "Lists, inspects, health-checks, or proxies one allowlisted runtime tool" "MCP/HTTP"
    toolGateway -> localMcp "Invokes the first local read-only allowlisted tool" "MCP"
    toolGateway -> eventLedger "Appends execution and filtered-result evidence" "in-process/HTTP"

    magg -> contextForge "Proxies allowlisted gateway capability" "MCP/HTTP"
    magg -> dagger "Proxies allowlisted deterministic pipeline capability" "MCP/HTTP"
    magg -> treg "Proxies allowlisted catalog search or budgeted execution" "MCP/HTTP"

    renderer -> eventLedger "Appends response evidence" "in-process/HTTP"
    memoryGovernor -> memoryPlatform "Stores governed memory" "HTTPS"
    memoryGovernor -> eventLedger "Reads provenance and appends memory lifecycle evidence" "in-process/HTTP"
    eventLedger -> postgres "Stores append-only events" "SQL"
    hotState -> redis "Stores TTL-bound snapshots" "Redis protocol"
    eventLedger -> observability "Publishes versioned metrics and integrity state" "in-process/HTTP"
  }

  views {
    systemContext trs "Context" {
      include *
      autoLayout lr
    }

    container trs "Containers" {
      include *
      autoLayout lr
    }

    styles {
      element "Person" {
        shape Person
        background #438DD5
        color #ffffff
      }
      element "Software System" {
        background #2E6295
        color #ffffff
      }
      element "Container" {
        background #438DD5
        color #ffffff
      }
      element "Database" {
        shape Cylinder
      }
      element "External" {
        background #8E8E93
        color #ffffff
      }
    }
  }
}
