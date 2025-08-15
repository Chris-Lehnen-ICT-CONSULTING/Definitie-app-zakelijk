# Privé PyPI Server Setup voor AI Code Reviewer

## Optie 1: DevPI (Aanbevolen)

### Installatie
```bash
pip install devpi-server devpi-client
```

### Server starten
```bash
# Initialiseer
devpi-init
devpi-gen-config

# Start server
devpi-server --start --host 0.0.0.0 --port 3141
```

### Package uploaden
```bash
# Login en setup
devpi use http://localhost:3141
devpi user -c myuser password=mypass
devpi login myuser --password=mypass
devpi index -c myuser/stable bases=root/pypi
devpi use myuser/stable

# Upload package
devpi upload dist/*
```

### Installeren in andere projecten
```bash
pip install -i http://localhost:3141/myuser/stable/+simple/ ai-code-reviewer
```

## Optie 2: pypiserver (Simpeler)

### Setup
```bash
pip install pypiserver passlib
mkdir ~/pypi-packages
```

### Start server
```bash
pypi-server -p 8080 ~/pypi-packages
```

### Upload package
```bash
cp dist/* ~/pypi-packages/
```

### Installeren
```bash
pip install --index-url http://localhost:8080/simple/ ai-code-reviewer
```

## Optie 3: Nexus Repository

Voor enterprise omgevingen:
1. Installeer Nexus Repository Manager
2. Maak een PyPI hosted repository
3. Upload met twine:
   ```bash
   twine upload --repository-url http://nexus.company.com/repository/pypi-internal/ dist/*
   ```

## Pip Configuratie

Maak `~/.pip/pip.conf`:
```ini
[global]
index-url = http://localhost:3141/myuser/stable/+simple/
extra-index-url = https://pypi.org/simple/
trusted-host = localhost
```