# NetScope — Cisco Topology Visualizer

Tool web che analizza configurazioni Cisco IOS e genera grafi di topologia interattivi tramite AI.

## Stack
- **Frontend**: HTML/CSS/JS + Cytoscape.js
- **Backend**: Azure Functions (Python)
- **AI**: Anthropic Claude API
- **Deploy**: Azure Static Web Apps + GitHub Actions

## Come funziona
1. Incolla una `show running-config` nel tool
2. La richiesta va alla Azure Function (`/api/analyze`)
3. La Function chiama l'API Anthropic con un prompt di parsing
4. Il JSON risultante viene visualizzato come grafo interattivo con Cytoscape.js

## Setup locale
```bash
pip install azure-functions-core-tools
cd api
func start
```
Apri `frontend/index.html` nel browser (con la Function in esecuzione).

## Deploy su Azure
1. Crea una Azure Static Web App dal portale Azure
2. Collega il repository GitHub
3. Imposta `ANTHROPIC_API_KEY` nelle Application Settings
4. Ogni push su `main` triggera il deploy automatico via GitHub Actions

## Struttura progetto
```
netscope/
├── frontend/
│   └── index.html
├── api/
│   ├── analyze/
│   │   ├── __init__.py
│   │   └── function.json
│   ├── host.json
│   └── requirements.txt
├── staticwebapp.config.json
├── .github/workflows/deploy.yml
└── README.md
```
