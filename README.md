# Flight Simulator MODULAR UI V0.1

Interfaccia grafica modulare per un simulatore di volo, costruita con **Python** e **PySide6 (Qt 6)**.

Il progetto gestisce esclusivamente la **componente visiva e l'interazione UI**: la fisica e la logica
di simulazione sono demandate a un modulo backend separato, collegabile tramite adapter dedicato.

---

## Indice

1. [Struttura del pacchetto](#struttura-del-pacchetto)
2. [Avvio e dipendenze](#avvio-e-dipendenze)
3. [Fasi di sviluppo completate](#fasi-di-sviluppo-completate)
4. [Sistema di temi](#sistema-di-temi)
5. [Catalogo strumenti](#catalogo-strumenti)
6. [Sistema di unità di misura](#sistema-di-unità-di-misura)
7. [Telemetria e integrazione backend](#telemetria-e-integrazione-backend)
8. [Hangar e barra di ricerca](#hangar-e-barra-di-ricerca)
9. [Controlli e scorciatoie](#controlli-e-scorciatoie)
10. [Status bar](#status-bar)
11. [Persistenza layout](#persistenza-layout)
12. [Prestazioni](#prestazioni)
13. [Prossimi passi](#prossimi-passi)

---

## Struttura del pacchetto

```
sim_ui/
├── __init__.py
├── main.py                     # Entry point
│
├── core/                       # Logica trasversale
│   ├── __init__.py
│   ├── constants.py            # MIME type, griglia, versione schema
│   ├── prototype.py            # InstrumentPrototype + InstrumentRegistry
│   ├── units.py                # UnitDefinition + definizioni unità
│   ├── telemetry.py            # TelemetryData + adapter (Mock/External)
│   └── theme.py                # InstrumentTheme + ThemeRegistry
│
├── instruments/                # Strumenti grafici
│   ├── __init__.py
│   ├── base.py                 # BaseInstrument, UnitButtonsMixin, Placeholder
│   ├── circular.py             # CircularGauge (gauge circolare con tema)
│   ├── specific.py             # Strumenti stile BASE + digitali
│   ├── professional.py         # Strumenti stile PROFESSIONAL
│   └── factory.py              # InstrumentFactory (type_id → classe)
│
└── ui/                         # Interfaccia
    ├── __init__.py
    ├── hangar_instr.py         # Hangar con barra di ricerca + drag&drop
    ├── scene.py                # InstrumentScene (griglia, snap)
    ├── view.py                 # InstrumentGraphicsView + FPSCounter
    └── window.py               # MainWindow (menu, toolbar, editing, persistenza)
```

### Responsabilità dei moduli

| Modulo | Responsabilità |
|---|---|
| `core/constants.py` | Costanti globali (MIME, griglia, schema) |
| `core/prototype.py` | Definizione prototipi e catalogo strumenti |
| `core/units.py` | Definizioni unità di misura e fattori di conversione |
| `core/telemetry.py` | Struttura dati telemetria e adapter |
| `core/theme.py` | Parametri visivi centralizzati |
| `instruments/base.py` | Classe base, mixin unità, placeholder |
| `instruments/circular.py` | Gauge circolare generica riutilizzabile |
| `instruments/specific.py` | Strumenti Base e digitali |
| `instruments/professional.py` | Strumenti con design professionale |
| `instruments/factory.py` | Mappatura type_id → classe concreta |
| `ui/hangar_instr.py` | Pannello laterale con ricerca e drag |
| `ui/scene.py` | Scena grafica con griglia |
| `ui/view.py` | Vista con zoom, pan, drop, OpenGL, FPS |
| `ui/window.py` | Finestra principale, menu, toolbar, editing |

---

## Avvio e dipendenze

### Dipendenze (`requirements.txt`)

```
PySide6>=6.5.0
```

> QtOpenGLWidgets è incluso nel pacchetto PySide6. Non servono dipendenze aggiuntive.

### Avvio

```bash
python -m sim_ui
# oppure
python -m sim_ui.main
```

---

## Fasi di sviluppo completate

| Fase | Contenuto | Stato |
|---|---|---|
| 1 | Canvas MVP (scena + placeholder) | ✅ |
| 2 | Catalogo e Hangar | ✅ |
| 3 | Drag & Drop | ✅ |
| 4 | Editing layout, snap, context menu, toolbar | ✅ |
| 5 | Persistenza JSON | ✅ |
| 6 | Rendering QPainter + strumenti reali | ✅ |
| 7 | Adapter telemetria + API backend | ✅ |
| 8 | Zoom/Pan/RubberBand/Fullscreen/OpenGL/FPS/Stress test/FPS target | ✅ |
| Step 2 | Grafica: temi, stili strumenti, Hangar migliorato | 🔄 In corso |

---

## Sistema di temi

### Architettura

- **`InstrumentTheme`** (dataclass): contiene tutti i parametri visivi.
- **`ThemeRegistry`**: catalogo dei temi con tema di default.
- **`BaseInstrument.set_theme()` / `theme()`**: assegna/legge il tema con invalidazione cache.
- **Menu "Tema"** nel MainWindow per cambio a runtime.

### Campi del tema

| Gruppo | Campi |
|---|---|
| Bezel | `bezel_color`, `bezel_ring_color` |
| Quadrante | `dial_color` |
| Tacche | `tick_major_color`, `tick_minor_color`, `tick_major_width`, `tick_minor_width` |
| Testo | `text_color`, `text_secondary_color`, `text_tertiary_color`, `font_family`, `font_size_*` |
| Lancette | `needle_color`, `needle_hub_color` |
| Attitude | `sky_color`, `ground_color`, `horizon_color`, `pitch_ladder_color` |
| Riferimenti | `reference_color`, `aircraft_symbol_color` |
| Scena | `selection_color`, `scene_background`, `grid_color` |

### Temi definiti

| Tema | Descrizione |
|---|---|
| **Base** | Stile originale (default) |
| **Night** | Toni blu scuro con accenti ciano (test) |

> **Nota**: gli stili *Professional*, *Clean* e *Comfort* non sono temi di colore ma
> **strumenti ridisegnati** con design proprio (classi separate).

---

## Catalogo strumenti

### Stili disponibili

| Stile | Descrizione | Stato |
|---|---|---|
| **Base** | Stile originale, colori piatti | ✅ Completo |
| **Professional** | Bezel metallico, viti, effetto vetro, dettagli | 🔄 Parziale |
| **Digital** | Display digitali con nastro scorrevole | ✅ Parziale |
| **Clean** (Light/Dark) | Minimal e pulito | ⬜ Da fare |
| **Comfort** (Orange/Green) | Anti-affaticamento visivo | ⬜ Da fare |

### Strumenti — Volo

| Strumento | type_id | Stile | Dim. | Unità | Note |
|---|---|---|---|---|---|
| Airspeed | `flight-airspeed` | Base | 200×200 | KT/KMH/MPH/MS | CircularGauge |
| Airspeed Pro | `flight-airspeed-pro` | Professional | 200×200 | KT/KMH/MPH/MS | Archi colorati, contrappeso |
| Altimeter | `flight-altimeter` | Base | 200×200 | FT/M | Due lancette |
| Altimeter Pro | `flight-altimeter-pro` | Professional | 200×200 | FT/M | Finestrella migliaia |
| Altimeter Digital | `flight-altimeter-digital` | Digital | 70×150 | FT/M | Nastro + freccia colorata |
| VSI Pro | `flight-vsi-pro` | Professional | 200×200 | FPM/MS | Scala UP/DOWN |
| VSI Digital | `flight-vsi-digital` | Digital | 70×150 | FPM/MS | Numero con segno |
| Attitude | `flight-attitude` | Base | 220×220 | — | Orizzonte semplice |
| Attitude Full | `flight-attitude-full` | Base | 240×240 | — | Scale pitch/roll |
| Attitude Square | `flight-attitude-square` | Base | 240×240 | — | Quadrato, ±180° |

### Strumenti — Motore

| Strumento | type_id | Stile | Dim. | Note |
|---|---|---|---|---|
| RPM | `engine-rpm` | Base | 200×200 | CircularGauge |
| Oil Temp | `engine-oil-temp` | Base | 180×180 | CircularGauge |

### Strumenti — Navigazione

| Strumento | type_id | Stile | Dim. | Note |
|---|---|---|---|---|
| Heading | `nav-heading` | Base | 200×200 | Bussola rotante |
| Heading Pro | `nav-heading-pro` | Professional | 200×200 | Rosa dettagliata, N rosso |

### Caratteristiche strumenti Professional

| Caratteristica | Base | Professional |
|---|---|---|
| Bezel | Colore piatto | Gradiente metallico radiale |
| Viti | Nessuna | 4 viti decorative a 45°/135°/225°/315° |
| Spessore bezel | 6-10 px | 3 px (`dial_r = outer_r - 3`) |
| Viti posizionate a | — | `screw_r = dial_r + 1` |
| Lancetta | Triangolo semplice | Triangolo + contrappeso |
| Effetto vetro | Assente | Arco riflesso semi-trasparente |
| Cappuccio | Colore piatto | Gradiente radiale |
| Numeri | Standard | Più grandi, bold |

### Caratteristiche strumenti Digital

| Caratteristica | Descrizione |
|---|---|
| Formato | Rettangolare stretto (70×150) |
| Nastro | Numeri scorrevoli con opacità decrescente |
| Box principale | Numero grande in Consolas bold |
| Freccia direzionale | Verde (salita) / Rosso-arancio (discesa) / Bianco (neutro) |
| Etichetta unità | In basso |

### Caratteristiche VSI Professional

| Caratteristica | Descrizione |
|---|---|
| Scala | 0 a ore 9, +170° salita, -170° discesa |
| Range | ±2000 FT/MIN oppure ±10 M/S |
| Etichette | "UP" e "DOWN" |
| Tacche | Maggiori ogni 500 fpm (o 2 m/s), minori intermedie |

---

## Sistema di unità di misura

### Meccanismo

Ogni strumento che supporta il cambio unità ha due pulsanti disegnati in alto a destra:
- **Pulsante tondo**: passa all'unità successiva in rotazione.
- **Pulsante triangolare** (punta in basso): apre il menu con la lista delle unità.

I pulsanti non interferiscono con il drag dello strumento.

### Implementazione

- **`UnitButtonsMixin`**: gestisce pulsanti, hit-test, menu, cambio unità.
- **`UnitDefinition`** (dataclass): `unit_id`, `label`, `factor`, `decimals`, `major_step`.
- **`init_units(units, index)`**: inizializza le unità disponibili.
- **`_on_unit_changed()`**: callback per aggiornare lo strumento.
- **`current_unit()`**: restituisce l'unità attiva.

### Unità definite

| Grandezza | Costante | Unità | Fattore | Strumenti |
|---|---|---|---|---|
| Velocità | `AIRSPEED_UNITS` | KNOTS, KM/H, MPH, M/S | 1.0, 1.852, 1.15078, 0.514444 | Airspeed, Airspeed Pro |
| Altitudine | `ALTITUDE_UNITS` | FEET, METERS | 1.0, 0.3048 | Altimeter, Altimeter Pro, Altimeter Digital |
| Velocità verticale | `VSI_UNITS` | FT/MIN, M/S | 1.0, 0.00508 | VSI Pro, VSI Digital |

> L'unità selezionata **non è ancora persistita** nel layout JSON.

---

## Telemetria e integrazione backend

### Struttura dati

```python
@dataclass
class TelemetryData:
    airspeed: float = 0.0
    altitude: float = 0.0
    rpm: float = 0.0
    oil_temp: float = 0.0
    heading: float = 0.0
    pitch: float = 0.0
    roll: float = 0.0
    manifold_pressure: float = 0.0
    fuel_flow: float = 0.0
    vertical_speed: float = 0.0
```

### Adapter

| Adapter | Descrizione |
|---|---|
| `MockTelemetryAdapter` | Dati sinusoidali simulati, frequenza regolabile |
| `ExternalTelemetryAdapter` | Riceve dati dal backend reale via `push_data()` |

### Gestione FPS target

Dal menu **Prestazioni → FPS Target**:

| FPS | Intervallo |
|---|---|
| 60 | ~16 ms |
| 40 | 25 ms |
| 30 | ~33 ms |
| **20** (default) | 50 ms |
| 15 | ~66 ms |
| 10 | 100 ms |

### API backend

```python
adapter = main_window.get_external_adapter()
adapter.push_data({"airspeed": 145.0, "altitude": 4200.0, ...})
# oppure
adapter.push_data(TelemetryData(airspeed=145.0, altitude=4200.0, ...))
```

---

## Hangar e barra di ricerca

### Struttura

Il dock Hangar contiene:
1. **Barra di ricerca** (QLineEdit) — sempre visibile in alto
2. **Lista strumenti** (QListWidget) — raggruppati per categoria

### Barra di ricerca

- **Sempre visibile**: parte fissa del dock, non sparisce mai.
- **Nell'ingombro laterale**: si adatta alla larghezza del dock.
- **Filtra per**: nome visualizzato, type_id, descrizione (tooltip).
- **Categorie**: le intestazioni spariscono se nessuno strumento corrisponde.
- **Pulsante ✗**: pulisce la ricerca.

### Interazione

- **Doppio-click**: aggiunge lo strumento al centro della vista.
- **Drag & drop**: trascina lo strumento nella posizione desiderata.

---

## Controlli e scorciatoie

### Interazione con la scena

| Input | Azione |
|---|---|
| `Ctrl + Rotella` | Zoom (ancorato al mouse) |
| `Tasto centrale + drag` | Pan della scena |
| `Drag su area vuota` | Selezione multipla (rubber band) |
| `Click sinistro su strumento` | Selezione + drag |
| `Click destro` | Menu contestuale |

### Scorciatoie tastiera

| Scorciatoia | Azione |
|---|---|
| `Ctrl + =` | Zoom in |
| `Ctrl + -` | Zoom out |
| `Ctrl + 0` | Reset zoom |
| `Ctrl + F` | Adatta tutto alla vista |
| `F11` | Fullscreen |
| `Ctrl + D` | Duplica selezionati |
| `Ctrl + A` | Seleziona tutto |
| `Ctrl + G` | Toggle snap/griglia |
| `Delete` | Elimina selezionati |
| `Ctrl + S` | Salva layout |
| `Ctrl + O` | Carica layout |

### Menu

| Menu | Voci |
|---|---|
| **File** | Salva, Carica, Pulisci, Esci |
| **Vista** | Zoom In/Out/Reset, Adatta, Fullscreen, OpenGL |
| **Tema** | Base, Night |
| **Telemetria** | Mock, Esterna, Pausa |
| **Prestazioni** | FPS Target, Stress test (+10/+50/+100), Pulisci |

### Toolbar di editing

Duplica | Elimina | Davanti | Dietro | Rot+15° | Rot-15° | Scala+ | Scala- | Reset | Snap

### Menu contestuale (su strumento)

Duplica | Porta davanti/dietro | Ruota ±15° | Scala ± | Reset | Elimina

### Menu contestuale (su area vuota)

Snap | Seleziona tutto | Deseleziona | Elimina selezionati

---

## Status bar

| Posizione | Contenuto | Comportamento |
|---|---|---|
| **Destra** (permanente) | Strum, FPS, Snap, Zoom, GL/SW, XY, Selezione | Sempre visibile |
| **Sinistra** (temporanea) | Messaggi azioni (salvataggio, cambio tema, ecc.) | Scompare dopo timeout |

Implementazione:
- Info permanenti: `QLabel` aggiunto con `addPermanentWidget()`.
- Messaggi temporanei: `statusBar().showMessage(text, timeout)`.

---

## Persistenza layout

### Formato JSON

```json
{
  "schema_version": 1,
  "snap_enabled": false,
  "grid_size": 20.0,
  "instruments": [
    {
      "instance_id": "uuid-qui",
      "type_id": "flight-airspeed-pro",
      "x": 120.0,
      "y": 200.0,
      "rotation": 0.0,
      "scale": 1.0,
      "z": 0.0
    }
  ]
}
```

### Campi salvati per strumento

| Campo | Descrizione |
|---|---|
| `instance_id` | UUID univoco dell'istanza |
| `type_id` | Tipo di strumento (collegamento al registry) |
| `x`, `y` | Posizione nella scena |
| `rotation` | Rotazione in gradi |
| `scale` | Fattore di scala |
| `z` | Z-order (profondità) |

### Non ancora persistiti

- Unità di misura selezionata per strumento
- Tema attivo

---

## Prestazioni

### Ottimizzazioni implementate

| Ottimizzazione | Descrizione |
|---|---|
| Cache sfondo | `paint_background` renderizzato una volta in QPixmap |
| MinimalViewportUpdate | Ridisegna solo le aree cambiate |
| OpenGL opzionale | Rendering GPU con fallback software |
| FPS Counter | Misura la frequenza di aggiornamento reale |
| FPS Target | Regola la frequenza del mock adapter |
| Stress test | Genera 10/50/100 strumenti per test di carico |

### Viewport OpenGL

Attivabile da **Vista → OpenGL**:
- Usa `QOpenGLWidget` come viewport della `QGraphicsView`.
- Fallback automatico se `PySide6.QtOpenGLWidgets` non è disponibile.
- Indicatore GL/SW nella status bar.

---

## Prossimi passi

### Priorità alta
1. Completare strumenti **Professional** mancanti (RPM Pro, Oil Temp Pro, Attitude Pro)
2. Stile **Clean** (Light/Dark)
3. Stile **Comfort** (Orange/Green)

### Priorità media
4. Thumbnail nell'Hangar per identificare visivamente gli strumenti
5. Filtro per stile nell'Hangar (tutti / Base / Pro / Digital / Clean / Comfort)
6. Persistenza dell'unità di misura nel JSON
7. Persistenza del tema attivo nel JSON

### Priorità bassa
8. Anteprima pannello / Cockpit Preview (modalità senza editor)
9. Preset di pannello salvabili
10. Culling / LOD per ottimizzazione con molti strumenti
11. Fase 9: interazione strumenti (knob, popup, toggle) — rimandata

---

## Note architetturali

### Separazione Base/Professional/Digital

Gli stili non sono temi applicati agli stessi strumenti, ma **classi separate** con design proprio:
- `specific.py` contiene gli strumenti Base e Digital
- `professional.py` contiene gli strumenti Professional
- Ogni stile ha il proprio `type_id` nel registry

### Ruolo del tema

Il sistema di temi (`theme.py`) influenza:
- Gli strumenti **Base** (tramite `CircularGauge` e strumenti custom)
- Il bordo di selezione
- Lo sfondo della scena e la griglia

Gli strumenti **Professional** hanno colori hardcoded nel loro design e non usano il tema.

### Factory e Registry

- **Registry** (`core/prototype.py`): catalogo statico dei prototipi.
- **Factory** (`instruments/factory.py`): crea l'istanza grafica dal `type_id`.
- Per aggiungere un nuovo strumento: registrare nel registry + mappare nella factory.
