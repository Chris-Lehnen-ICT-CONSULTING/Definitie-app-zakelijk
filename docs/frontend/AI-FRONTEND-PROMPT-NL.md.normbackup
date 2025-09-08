# 🎯 AI Frontend Generatie Prompt voor DefinitieAgent

## Meesterlijke Prompt voor AI-Gedreven Frontend Ontwikkeling

### 🌐 Hoofddoel
Creëer een moderne, responsieve webapplicatie voor DefinitieAgent - een geavanceerd Nederlands juridisch definitiebeheerssysteem dat juridische professionals helpt bij het maken, valideren en beheren van gestandaardiseerde juridische terminologiedefinities met AI-ondersteuning, kwaliteitscontrole en samenwerkingsworkflows.

### 📋 Gedetailleerde Stap-voor-Stap Instructies

1. **Initialiseer een Next.js 14 applicatie** met TypeScript, Tailwind CSS, en Shadcn/ui componenten
2. **Stel de projectstructuur in** met de volgende mappen:
   - `/app` - App router pagina's en layouts
   - `/components` - Herbruikbare UI componenten georganiseerd per functie
   - `/lib` - Utilities, API clients, en businesslogica
   - `/hooks` - Aangepaste React hooks voor state en effecten
   - `/types` - TypeScript type definities
   - `/styles` - Globale stijlen en Tailwind configuratie

3. **Maak de hoofdlayout** (`/app/layout.tsx`):
   - Vaste header met app-branding "DefinitieAgent" en versie-indicator
   - Responsieve navigatie die inklapt naar hamburgermenu op mobiel
   - Footer met snelle links en systeemstatus indicator
   - Gebruik Inter lettertype voor bodytekst en Geist Mono voor code/definities

4. **Implementeer de globale context configuratiebalk** (boven hoofdinhoud):
   - Begrip invoerveld met Nederlands label "Begrip" - verplicht veld met validatie
   - Multi-select dropdown voor "Context Organisatie"
   - Multi-select dropdown voor "Wettelijke Context"
   - Multi-select dropdown voor "Wettelijke Grondslag"
   - Document uploadzone met drag-and-drop ondersteuning voor PDF, Word, CSV, JSON, HTML

5. **Bouw het tabnavigatie systeem** met deze 9 tabs:
   - 🚀 Definitie Generatie - PRIMAIRE TAB
   - 👨‍💼 Expert Review
   - 📜 Geschiedenis
   - 📤 Export & Beheer
   - 🔧 Kwaliteitscontrole
   - 🔌 Externe Bronnen
   - 📈 Monitoring
   - 🔍 Web Lookup
   - 🛠️ Management

6. **Implementeer de Definitie Generatie tab** (primaire workflow):
   - Snelle actieknoppen: "Genereer Definitie", "Controleer Duplicaten", "Wis Velden"
   - Resultatenweergavegebied met:
     - Gegenereerde definitietekst (alleen-lezen met kopieerknop)
     - Opschoning vergelijkingsweergave (origineel vs opgeschoond naast elkaar)
     - Validatieresultaten met kleurgecodeerde indicatoren
     - Synoniemen, antoniemen, en voorbeeldzinnen secties
     - Bronreferenties met klikbare links
   - Debug modus schakelaar die technische details toont

7. **Creëer de Expert Review tab**:
   - Lijstweergave van definities in afwachting van beoordeling
   - Detailweergave met inline bewerkingsmogelijkheden
   - Goedkeuring/afwijzing workflow met opmerkingen
   - Versievergelijkingstools

8. **Bouw de Geschiedenis tab**:
   - Doorzoekbare, sorteerbare tabel van alle definities
   - Filters op datum, status, maker, categorie
   - Snelle acties: bekijken, bewerken, dupliceren, verwijderen
   - Exporteer geselecteerde items functionaliteit

9. **Ontwerp het Kwaliteitscontrole dashboard**:
   - Metriekkaarten met slaag/faal percentages
   - Regelovertreding uitsplitsing grafiek
   - Recente validatieresultaten tijdlijn
   - Configureerbaar testregelbeheer

10. **Stijl met mobile-first responsief ontwerp**:
    - Mobiel (<768px): Enkele kolom, inklapbare secties, ondernavigatie
    - Tablet (768-1024px): Twee-kolom layouts waar geschikt
    - Desktop (>1024px): Volledige multi-kolom layouts met zijbalken

### 💻 Codevoorbeelden, Datastructuren & Beperkingen

#### API Contract Structuur:
```typescript
// Definitie Generatie Verzoek
interface GenereerDefinitieVerzoek {
  begrip: string;
  context: {
    organisatie: string[];
    wettelijk: string[];
    wettelijkeGrondslag: string[];
  };
  documenten?: GeuploadDocument[];
}

// Definitie Response
interface DefinitieResponse {
  id: string;
  begrip: string;
  definitie: string;
  opgeschoondeDefinitie?: string;
  synoniemen: string[];
  antoniemen: string[];
  voorbeelden: string[];
  bronnen: Bron[];
  validatie: ValidatieResultaat;
  categorie: OntologischeCategorie;
  metadata: {
    aangemaakt: string;
    aangemaaktDoor: string;
    versie: number;
  };
}

// Validatie Resultaat
interface ValidatieResultaat {
  geslaagd: boolean;
  score: number;
  regels: RegelResultaat[];
}
```

#### Component Voorbeeld - Definitie Weergave:
```tsx
// components/definitie/DefinitieWeergave.tsx
export function DefinitieWeergave({ definitie }: { definitie: DefinitieResponse }) {
  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>{definitie.begrip}</span>
          <Badge variant={definitie.validatie.geslaagd ? "success" : "destructive"}>
            {definitie.validatie.score}% Geldig
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div>
            <Label>Definitie</Label>
            <p className="mt-1 text-sm text-gray-700">{definitie.definitie}</p>
          </div>
          {/* Aanvullende secties */}
        </div>
      </CardContent>
    </Card>
  );
}
```

#### State Management Patroon:
```typescript
// Gebruik Zustand voor globale state
import { create } from 'zustand';

interface AppState {
  huidigBegrip: string;
  context: Context;
  definities: DefinitieResponse[];
  isLaden: boolean;
  setBegrip: (begrip: string) => void;
  setContext: (context: Partial<Context>) => void;
  genereerDefinitie: () => Promise<void>;
}

const useAppStore = create<AppState>((set, get) => ({
  // Implementatie
}));
```

#### Ontwerpsysteem Kleuren:
```css
/* Tailwind config uitbreiding */
colors: {
  primair: {
    50: '#eff6ff',
    500: '#3b82f6',
    900: '#1e3a8a'
  },
  succes: '#10b981',
  waarschuwing: '#f59e0b',
  fout: '#ef4444',
  info: '#3b82f6'
}
```

#### Nederlandse UI Tekst Constanten:
```typescript
export const UI_TEKST = {
  knoppen: {
    genereer: "Genereer Definitie",
    controleerDuplicaten: "Controleer Duplicaten",
    wis: "Wis Velden",
    exporteer: "Exporteer",
    opslaan: "Opslaan"
  },
  labels: {
    begrip: "Begrip",
    definitie: "Definitie",
    context: "Context",
    validatie: "Validatie",
    bronnen: "Bronnen"
  },
  berichten: {
    laden: "Bezig met laden...",
    succes: "Definitie succesvol gegenereerd",
    fout: "Er is een fout opgetreden"
  }
};
```

### 🚫 Beperkingen & Grenzen

**NIET DOEN:**
- Backend API contracten of database schema's wijzigen
- Andere UI bibliotheek gebruiken dan Shadcn/ui en Tailwind CSS
- Authenticatie/autorisatie implementeren (wordt door backend afgehandeld)
- Nieuwe API endpoints maken (alleen bestaande consumeren)
- Nederlandse terminologie of juridische taalpatronen wijzigen
- Animaties toevoegen die kunnen afleiden van professioneel gebruik
- localStorage gebruiken voor gevoelige data (gebruik veilige sessie opslag)

**ALLEEN WIJZIGEN:**
- Bestanden in de `/app`, `/components`, `/lib`, `/hooks`, `/types` mappen
- Tailwind configuratie voor aangepaste design tokens
- Publieke assets in `/public` map
- Omgevingsvariabelen in `.env.local` voor API endpoints

**MOET BEVATTEN:**
- TypeScript strict mode voor alle componenten
- Error boundaries voor elegante foutafhandeling
- Laadstaten voor alle asynchrone operaties
- Toegankelijkheidsfuncties (ARIA labels, toetsenbordnavigatie)
- Nederlandse taal voor alle gebruikersteksten
- Responsief ontwerp voor alle schermformaten
- Printvriendelijke stijlen voor definitie exports

### 🎨 Visuele Ontwerprichtlijnen

**Kleurenpalet:**
- Primair: Professioneel blauw (#3b82f6)
- Achtergrond: Lichtgrijs (#f9fafb) met witte kaarten
- Tekst: Donkergrijs (#1f2937) voor hoog contrast
- Succes: Groen (#10b981)
- Waarschuwing: Oranje (#f59e0b)
- Fout: Rood (#ef4444)

**Typografie:**
- Koppen: Inter lettertype, semi-bold
- Body: Inter lettertype, regular
- Definities: Geist Mono of vergelijkbaar monospace
- Regelafstand: 1.5 voor leesbaarheid

**Spacing:**
- Gebruik 4px grid systeem (space-1 = 4px)
- Kaart padding: 16-24px
- Sectie marges: 32px
- Consistente afstand tussen elementen

**Component Stijl:**
- Afgeronde hoeken (8px voor kaarten, 6px voor knoppen)
- Subtiele schaduwen voor diepte
- Duidelijke focus staten voor toegankelijkheid
- Hover staten voor alle interactieve elementen

### 🔧 Technische Vereisten

**Prestaties:**
- Lazy load zware componenten
- Implementeer virtueel scrollen voor lange lijsten
- Gebruik React.memo voor dure componenten
- Debounce zoekinvoer (300ms)
- Cache API responses met SWR of React Query

**Browser Ondersteuning:**
- Chrome/Edge (laatste 2 versies)
- Firefox (laatste 2 versies)
- Safari 14+
- Mobiele browsers (iOS Safari, Chrome Android)

**Test Aanpak:**
- Unit tests voor utilities en hooks
- Component tests met React Testing Library
- E2E tests voor kritieke gebruikersflows
- Toegankelijkheidstests met axe-core

### 📱 Mobile-First Breekpunten

```scss
// Mobile First Aanpak
// Standaard: Mobiel (<768px)
.component {
  // Mobiele stijlen
}

// Tablet (≥768px)
@media (min-width: 768px) {
  .component {
    // Tablet overschrijvingen
  }
}

// Desktop (≥1024px)
@media (min-width: 1024px) {
  .component {
    // Desktop overschrijvingen
  }
}
```

---

## 🚀 Aan de Slag Instructies

Bij het gebruik van deze prompt met een AI frontend tool:

1. **Verstrek deze volledige prompt** om context vast te stellen
2. **Begin met het genereren van de projectstructuur** en core layout
3. **Focus op één tab tegelijk**, beginnend met Definitie Generatie
4. **Test elk component** voordat je naar de volgende gaat
5. **Itereer op styling** nadat functionaliteit compleet is
6. **Voeg verfijning toe** (animaties, transities) als laatste touches

## ⚠️ Belangrijke Opmerkingen

- Deze applicatie behandelt juridische definities die precisie en professionaliteit vereisen
- Alle gegenereerde code moet worden beoordeeld op veiligheid en naleving
- De AI moet consistentie behouden met Nederlandse juridische terminologie
- Focus op bruikbaarheid boven flitsend ontwerp - dit is een professioneel hulpmiddel
- Zorg dat alle formulieren juiste validatie hebben voor indiening
- Overweeg dat de applicatie dagelijks door juridische professionals wordt gebruikt

Onthoud: AI-gegenereerde code is een startpunt. Altijd beoordelen, testen en verfijnen voor productie-implementatie.
