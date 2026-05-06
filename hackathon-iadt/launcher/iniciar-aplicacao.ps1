#Requires -Version 5.1
<#
.SYNOPSIS
  Launcher do projeto hackathon-iadt: sobe todos os containers Docker e prepara
  o ambiente para que a aplicacao fique pronta para uso.
.DESCRIPTION
  Verifica pre-requisitos (Docker Desktop), prepara o arquivo .env, executa
  docker compose build + up, aguarda os healthchecks e abre o Streamlit no
  navegador. Pensado para ser empacotado como .exe via ps2exe.
#>

# ----------------------------------------------------------------------------
# Configuracao
# ----------------------------------------------------------------------------
$ErrorActionPreference = 'Stop'
$Host.UI.RawUI.WindowTitle = 'Hackathon IADT - Launcher'

function Write-Step    { param([string]$m) Write-Host "`n==> $m" -ForegroundColor Cyan }
function Write-Ok      { param([string]$m) Write-Host "  [OK] $m" -ForegroundColor Green }
function Write-Warn    { param([string]$m) Write-Host "  [!]  $m" -ForegroundColor Yellow }
function Write-ErrLine { param([string]$m) Write-Host "  [X]  $m" -ForegroundColor Red }

function Pause-Exit {
    param([int]$Code = 0)
    Write-Host ''
    Write-Host 'Pressione qualquer tecla para fechar esta janela...' -ForegroundColor DarkGray
    try { [void][System.Console]::ReadKey($true) } catch { Start-Sleep -Seconds 5 }
    exit $Code
}

# ----------------------------------------------------------------------------
# Resolve diretorio do projeto (uma pasta acima do launcher)
# ----------------------------------------------------------------------------
if ($MyInvocation.MyCommand.Path) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
} else {
    # Quando rodando como .exe gerado pelo ps2exe
    $scriptDir = Split-Path -Parent ([System.Diagnostics.Process]::GetCurrentProcess().MainModule.FileName)
}
$projectRoot = Split-Path -Parent $scriptDir
if (-not (Test-Path (Join-Path $projectRoot 'docker-compose.yml'))) {
    # fallback: talvez o exe esteja na raiz
    if (Test-Path (Join-Path $scriptDir 'docker-compose.yml')) {
        $projectRoot = $scriptDir
    }
}

Write-Host '============================================================' -ForegroundColor Cyan
Write-Host '  Hackathon IADT - Inicializador da aplicacao'                 -ForegroundColor Cyan
Write-Host '============================================================' -ForegroundColor Cyan
Write-Host "  Diretorio do projeto: $projectRoot" -ForegroundColor DarkGray

if (-not (Test-Path (Join-Path $projectRoot 'docker-compose.yml'))) {
    Write-ErrLine "docker-compose.yml nao encontrado em $projectRoot"
    Write-ErrLine 'Coloque o executavel na pasta launcher/ do projeto ou na raiz.'
    Pause-Exit 1
}

Set-Location $projectRoot

# ----------------------------------------------------------------------------
# 1) Verificar Docker instalado
# ----------------------------------------------------------------------------
Write-Step '1/6 Verificando instalacao do Docker'
$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerCmd) {
    Write-ErrLine 'Docker nao encontrado no PATH.'
    Write-Host ''
    Write-Host 'Instale o Docker Desktop antes de continuar:' -ForegroundColor Yellow
    Write-Host '  https://www.docker.com/products/docker-desktop/' -ForegroundColor Yellow
    Write-Host ''
    Write-Host 'Apos instalar, reinicie o Windows e clique novamente neste executavel.' -ForegroundColor Yellow
    Pause-Exit 2
}
Write-Ok "Docker encontrado em $($dockerCmd.Source)"

# ----------------------------------------------------------------------------
# 2) Verificar engine Docker rodando (subir Docker Desktop se preciso)
# ----------------------------------------------------------------------------
Write-Step '2/6 Verificando se o Docker Desktop esta em execucao'
$dockerOk = $false
try {
    docker info --format '{{.ServerVersion}}' 1>$null 2>$null
    if ($LASTEXITCODE -eq 0) { $dockerOk = $true }
} catch { $dockerOk = $false }

if (-not $dockerOk) {
    Write-Warn 'Docker Engine nao esta respondendo. Tentando iniciar Docker Desktop...'
    $dockerDesktop = Join-Path $env:ProgramFiles 'Docker\Docker\Docker Desktop.exe'
    if (Test-Path $dockerDesktop) {
        Start-Process -FilePath $dockerDesktop | Out-Null
    } else {
        Write-ErrLine "Nao encontrei $dockerDesktop. Inicie o Docker Desktop manualmente."
        Pause-Exit 3
    }

    Write-Host '  Aguardando o Docker subir (pode demorar ate 90s)...' -ForegroundColor DarkGray
    $deadline = (Get-Date).AddSeconds(120)
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Seconds 3
        docker info --format '{{.ServerVersion}}' 1>$null 2>$null
        if ($LASTEXITCODE -eq 0) { $dockerOk = $true; break }
    }
}
if (-not $dockerOk) {
    Write-ErrLine 'Docker Desktop nao subiu a tempo. Inicie manualmente e tente de novo.'
    Pause-Exit 4
}
Write-Ok 'Docker Engine respondendo'

# ----------------------------------------------------------------------------
# 3) Garantir docker compose v2
# ----------------------------------------------------------------------------
Write-Step '3/6 Verificando Docker Compose v2'
docker compose version 1>$null 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-ErrLine "'docker compose' v2 nao disponivel. Atualize o Docker Desktop."
    Pause-Exit 5
}
Write-Ok 'docker compose v2 disponivel'

# ----------------------------------------------------------------------------
# 4) Preparar .env
# ----------------------------------------------------------------------------
Write-Step '4/6 Preparando arquivo .env'
$envPath     = Join-Path $projectRoot '.env'
$envExample  = Join-Path $projectRoot '.env.example'
if (-not (Test-Path $envPath)) {
    if (Test-Path $envExample) {
        Copy-Item $envExample $envPath
        Write-Ok '.env criado a partir de .env.example'
        Write-Warn 'EDITE o .env e preencha ANTHROPIC_API_KEY / OPENAI_API_KEY antes de usar a IA.'
    } else {
        Write-Warn '.env nao existe e .env.example tambem nao foi encontrado. Continuando com defaults.'
    }
} else {
    Write-Ok '.env ja existe (mantido)'
}

# ----------------------------------------------------------------------------
# 5) Build + up dos containers
# ----------------------------------------------------------------------------
Write-Step '5/6 Construindo imagens e subindo containers (pode demorar na 1a vez)'
docker compose pull 2>&1 | Out-Host
docker compose build  2>&1 | Out-Host
if ($LASTEXITCODE -ne 0) {
    Write-ErrLine 'Falha no build das imagens. Verifique os logs acima.'
    Pause-Exit 6
}
docker compose up -d  2>&1 | Out-Host
if ($LASTEXITCODE -ne 0) {
    Write-ErrLine 'Falha ao subir os containers. Verifique os logs acima.'
    Pause-Exit 7
}
Write-Ok 'Containers iniciados'

# ----------------------------------------------------------------------------
# 6) Aguardar healthcheck do Streamlit + abrir navegador
# ----------------------------------------------------------------------------
Write-Step '6/6 Aguardando aplicacao ficar disponivel em http://localhost:8501'
$ready = $false
$deadline = (Get-Date).AddSeconds(180)
while ((Get-Date) -lt $deadline) {
    try {
        $r = Invoke-WebRequest -Uri 'http://localhost:8501' -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
        if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500) { $ready = $true; break }
    } catch { Start-Sleep -Seconds 3 }
}
if ($ready) {
    Write-Ok 'Streamlit respondendo'
    Start-Process 'http://localhost:8501' | Out-Null
} else {
    Write-Warn 'Streamlit nao respondeu em 3min, mas containers ja estao em execucao.'
    Write-Warn 'Acompanhe com: docker compose logs -f streamlit-app'
}

# ----------------------------------------------------------------------------
# Status final
# ----------------------------------------------------------------------------
Write-Host ''
Write-Host '============================================================' -ForegroundColor Green
Write-Host '  Aplicacao no ar!'                                            -ForegroundColor Green
Write-Host '============================================================' -ForegroundColor Green
Write-Host '  Streamlit (UI) ........ http://localhost:8501'
Write-Host '  IA Service (FastAPI) .. http://localhost:8000/docs'
Write-Host '  Report API ............ http://localhost:8001/docs'
Write-Host '  RabbitMQ Management ... http://localhost:15672  (hackathon / hackathon123)'
Write-Host '  Postgres (pgvector) ... localhost:5432'
Write-Host '  Redis ................. localhost:6379'
Write-Host ''
Write-Host '  Para parar tudo:  docker compose down'           -ForegroundColor DarkGray
Write-Host '  Para ver logs:    docker compose logs -f'        -ForegroundColor DarkGray
Write-Host ''
Pause-Exit 0
