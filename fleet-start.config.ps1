# Per-repo fleet start config for learnbot-mcp
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'learnbot-mcp'
    BackendPort  = 11101
    FrontendPort = 11102
    HealthPath   = '/health'
    WebRoot      = 'webapp'
    Backend = @{
        Kind          = 'uvicorn'
        UvicornTarget = 'learnbot_mcp.api:app'
        SyncExtras    = @('dev')
        Env           = @{ WEB_PORT = '11101' }
    }
    Frontend = @{
        Kind           = 'vite-npm'
        PackageManager = 'npm'
        PortEnvVar     = 'VITE_PORT'
        ApiTargetEnv   = 'VITE_API_TARGET'
    }
}
