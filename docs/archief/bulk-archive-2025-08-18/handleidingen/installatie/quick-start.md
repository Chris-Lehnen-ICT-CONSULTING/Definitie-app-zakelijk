# 🚀 DefinitieAgent - Quick Start Guide

Deze guide helpt je om het DefinitieAgent project snel op te zetten en te draaien.

## 📋 Vereisten

- Python 3.8 of hoger
- pip (Python package manager)
- Git
- OpenAI API key

## 🛠️ Installatie Stappen

### 1. Clone het project

```bash
git clone <repository-url>
cd Definitie-app
```

### 2. Maak een virtuele omgeving (aanbevolen)

```bash
python -m venv venv

# Activeer de virtuele omgeving:
# Op macOS/Linux:
source venv/bin/activate

# Op Windows:
venv\Scripts\activate
```

### 3. Installeer dependencies

```bash
pip install -r requirements.txt
```

### 4. Configureer environment variables

```bash
# Kopieer de example file
cp .env.example .env

# Edit .env en voeg je OpenAI API key toe
# OPENAI_API_KEY=your_actual_api_key_here
```

### 5. Initialiseer de database

```bash
# De database wordt automatisch aangemaakt bij eerste run
# Of maak handmatig:
mkdir -p data
python -c "from src.repositories.base import init_db; init_db()"
```

### 6. Start de applicatie

```bash
streamlit run src/app.py
```

De applicatie opent automatisch in je browser op http://localhost:8501

## 🔧 Configuratie

### Belangrijkste settings in `.env`:

- `OPENAI_API_KEY` - **Verplicht**: Je OpenAI API key
- `OPENAI_MODEL` - AI model (default: gpt-4-turbo-preview)
- `DEBUG` - Debug mode aan/uit
- `ENABLE_DEVELOPER_TOOLS` - Developer tab in UI

### Optionele configuratie:

- `OPENAI_TEMPERATURE` - AI creativiteit (0.0-1.0)
- `RATE_LIMIT_MAX_REQUESTS` - API rate limiting
- `CACHE_TTL` - Cache timeout in seconden

## 🐛 Troubleshooting

### Import errors
```bash
# Run vanuit project root:
cd /pad/naar/Definitie-app
python -m streamlit run src/app.py
```

### Database errors
```bash
# Check permissions:
ls -la data/
# Fix met:
chmod 755 data/
```

### OpenAI API errors
- Controleer je API key in `.env`
- Controleer je OpenAI account credits

### UI laadt niet
- Clear browser cache
- Probeer incognito/private mode
- Check console voor JavaScript errors

## 📚 Volgende Stappen

1. Lees de [Project README](README.md) voor features overzicht
2. Check de [Roadmap](../../archive/2025-01-12/root/ROADMAP.md) voor geplande features
3. Zie Contributing voor development guidelines
4. Browse de Architectuur docs

## 🆘 Hulp Nodig?

- Check de FAQ - *Coming soon*
- Zoek in [GitHub Issues](https://github.com/your-repo/issues)
- Contact het development team

---
*Laatste update: 17 juli 2025*
