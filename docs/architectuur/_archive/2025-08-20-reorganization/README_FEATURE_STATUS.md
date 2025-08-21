# Feature Status Dashboard - Handleiding

## 🔄 Hoe blijft de feature status up-to-date?

### Optie 1: GitHub Integration (Aanbevolen)
De feature status wordt automatisch gesynchroniseerd met GitHub Issues/Projects.

**Setup:**
1. Maak GitHub Issues voor elke feature
2. Gebruik labels voor epics (bijv. `epic:ui`, `epic:security`)
3. Gebruik Project board voor status tracking
4. GitHub Actions update automatisch de dashboard

**Voordelen:**
- ✅ Single source of truth
- ✅ Automatische updates
- ✅ Team kan samenwerken via GitHub
- ✅ Historie en audit trail

### Optie 2: Manual Update via Script
Draai het update script handmatig:

```bash
# Set environment variables
export GITHUB_TOKEN="your-github-token"
export GITHUB_REPO="username/repo"
export GITHUB_PROJECT_NUMBER="1"

# Run update
python scripts/update_feature_status.py
```

### Optie 3: Live API Dashboard
Voor real-time updates, start de API server:

```bash
# Install dependencies
pip install fastapi uvicorn

# Start API server
python src/api/feature_status_api.py

# Dashboard haalt nu live data op
```

## 📊 Dashboard Features

### Automatische Updates
- **GitHub Webhook**: Updates bij elke issue wijziging
- **Scheduled Updates**: Dagelijks om 9:00 AM
- **Manual Trigger**: Via GitHub Actions UI

### Data Bronnen
1. **GitHub Issues**: Feature items
2. **GitHub Projects**: Status tracking
3. **Labels**: Epic mapping en prioriteit

### Status Mapping
- `Todo` → Not Started
- `In Progress` → In Progress
- `Done` → Complete
- `Blocked` → Not Started

### Epic Labels
- `epic:basis-definitie` → Basis Definitie Generatie
- `epic:kwaliteit` → Kwaliteitstoetsing
- `epic:ui` → User Interface
- `epic:security` → Security & Authentication
- `epic:performance` → Performance
- `epic:export` → Export/Import
- `epic:web-lookup` → Web Lookup & Integration
- `epic:monitoring` → Monitoring & Analytics
- `epic:content` → Content Management

## 🚀 Quick Start

### Voor Product Owners
1. Bekijk dashboard: Open `ARCHITECTURE_VISUALIZATION_DETAILED.html`
2. Filter op status met de knoppen
3. Klik op epics voor details
4. Check "Last Updated" timestamp

### Voor Developers
1. Update feature status in GitHub Issues
2. Move cards in GitHub Project
3. Dashboard update automatisch (of trigger manual)

### Voor DevOps
1. Setup GitHub Actions workflow
2. Configure secrets: `GITHUB_TOKEN`
3. Monitor update logs in Actions tab

## 🔧 Troubleshooting

### Dashboard toont oude data
- Check GitHub Actions logs
- Verify GITHUB_TOKEN permissions
- Run manual update script

### Features ontbreken
- Check GitHub labels
- Verify epic mapping
- Ensure issues are in project

### API geeft errors
- Check CORS settings
- Verify JSON file exists
- Check server logs

## 📝 Best Practices

1. **Consistent Labeling**: Gebruik standaard labels
2. **Regular Updates**: Update status in GitHub direct
3. **Clear Descriptions**: Duidelijke feature namen
4. **Priority Labels**: Mark critical features
5. **Epic Assignment**: Elke feature in één epic

## 🔒 Security

- GitHub Token alleen in secrets
- API alleen read-only access
- CORS configured voor je domein
- No sensitive data in features
