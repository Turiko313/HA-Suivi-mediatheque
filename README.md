# 🎬 Suivi Médiathèque pour Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/Turiko313/HA-Suivi-mediatheque)](https://github.com/Turiko313/HA-Suivi-mediatheque/releases)

> Vous avez le 1 et le 3 d'une trilogie mais pas le 2 ?  
> Il vous manque des épisodes dans une série ou un anime ?  
> **Suivi Médiathèque** scanne vos disques et vous dit exactement ce qu'il manque.

---

## ✨ Fonctionnalités

| | Fonctionnalité |
|---|---|
| 🎥 | **Films** — Détecte les volets manquants dans les sagas et trilogies |
| 📺 | **Séries TV** — Repère les épisodes et saisons manquants |
| 🎌 | **Anime** — Idem, avec un chemin et un sensor dédiés |
| 🔄 | **Scan planifié** — Analyse automatique configurable (toutes les heures, jours, semaines…) |
| ▶️ | **Scan manuel** — Service `media_gap_analyzer.scan_now` pour lancer un scan immédiat |
| 📊 | **Sensors HA** — Nombre d'éléments manquants + détails complets dans les attributs |
| 💾 | **Multi-chemins** — Scannez plusieurs disques ou partages NAS |
| 🖥️ | **Config UI** — Configuration 100% via l'interface Home Assistant |
| 📦 | **HACS** — Installation en un clic via dépôt personnalisé |

---

## 📋 Pré-requis

1. **Home Assistant** 2024.1.0 ou supérieur
2. **Clé API TMDb** (gratuite) — Créez un compte sur [themoviedb.org](https://www.themoviedb.org/) puis rendez-vous dans *Paramètres → API* pour obtenir votre clé v3
3. **Médiathèque accessible** — Vos NAS / disques réseau doivent être montés comme dossiers locaux dans HA (via `/etc/fstab`, add-on Samba, montage `/media/`, etc.)

---

## 📥 Installation

### Via HACS (recommandé)

1. Ouvrez **HACS** dans Home Assistant
2. Menu **⋮** (3 points) → **Dépôts personnalisés**
3. Collez l'URL : `https://github.com/Turiko313/HA-Suivi-mediatheque`
4. Catégorie : **Intégration**
5. Cliquez **Ajouter**
6. Recherchez **« Suivi Médiathèque »** → **Télécharger**
7. **Redémarrez** Home Assistant

### Installation manuelle

1. Téléchargez le contenu du dossier `custom_components/media_gap_analyzer/`
2. Copiez-le dans `<config HA>/custom_components/media_gap_analyzer/`
3. Redémarrez Home Assistant

---

## ⚙️ Configuration

1. **Paramètres** → **Appareils et services** → **Ajouter une intégration**
2. Cherchez **« Suivi Médiathèque »**
3. Remplissez le formulaire :

| Champ | Description | Exemple |
|---|---|---|
| **Clé API TMDb** | Votre clé API v3 | `a1b2c3d4e5f6...` |
| **Langue** | Langue des résultats TMDb | `fr` |
| **Intervalle de scan** | En heures (1 à 720) | `24` (1 fois/jour) ou `168` (1 fois/semaine) |
| **Chemins des films** | Dossier(s) contenant vos films | `/media/films` |
| **Chemins des séries** | Dossier(s) contenant vos séries | `/media/series` |
| **Chemins des animés** | Dossier(s) contenant vos animes | `/media/anime` |

> 💡 **Plusieurs chemins ?** Séparez-les par des virgules : `/media/films,/mnt/nas2/films`

### Modifier plus tard

**Paramètres** → **Appareils et services** → **Suivi Médiathèque** → **Configurer**

---

## 📂 Organisation attendue de la médiathèque

### Films

Chaque film peut être un fichier ou un sous-dossier :

```
/media/films/
├── Inception (2010)/
│   └── Inception.mkv
├── The Matrix (1999).mkv
├── Le Seigneur des Anneaux - La Communauté de l'Anneau (2001)/
│   └── movie.mkv
└── Avatar.2009.1080p.BluRay.mkv
```

### Séries / Anime

Un dossier par série, avec optionnellement des sous-dossiers par saison.  
Les fichiers doivent contenir le pattern **`S01E01`** (ou `1x01`) dans leur nom.

```
/media/series/
├── Breaking Bad/
│   ├── Season 01/
│   │   ├── S01E01 - Pilot.mkv
│   │   ├── S01E02 - Cat's in the Bag.mkv
│   │   └── S01E03.mkv
│   └── Season 02/
│       └── S02E01.mkv
└── The Office/
    ├── S01E01.mkv
    └── S01E03.mkv    ← il manque le E02 !
```

### Formats vidéo supportés

`.mkv` `.mp4` `.avi` `.m4v` `.wmv` `.flv` `.mov` `.ts` `.iso` `.img` `.mpg` `.mpeg` `.divx` `.ogm` `.webm`

---

## 📊 Sensors créés

| Sensor | État | Attributs |
|---|---|---|
| **Films manquants** | Nombre de films manquants | Liste groupée par collection (saga/trilogie) |
| **Épisodes manquants (Séries)** | Nombre d'épisodes manquants | Liste groupée par série et saison |
| **Épisodes manquants (Anime)** | Nombre d'épisodes manquants | Liste groupée par anime et saison |
| **Dernier scan médiathèque** | Date/heure du dernier scan | Statistiques du scan |

### Exemple d'attributs — Films manquants

```yaml
missing_by_collection:
  "Le Seigneur des Anneaux - Trilogie":
    - "Le Seigneur des Anneaux : Les Deux Tours (2002)"
  "Matrix - Collection":
    - "Matrix Reloaded (2003)"
    - "Matrix Revolutions (2003)"
total_missing: 3
scanned: 42
collections_found: 6
```

### Exemple d'attributs — Épisodes manquants

```yaml
missing_by_series:
  "Breaking Bad":
    S01:
      - 4
      - 5
    S02:
      - 3
  "The Office":
    S01:
      - 2
total_missing: 4
scanned: 12
series_analyzed: 10
```

---

## 🔧 Service

### `media_gap_analyzer.scan_now`

Lance un scan immédiat de toute la médiathèque.

**Depuis le panneau développeur :**
- **Services** → `media_gap_analyzer.scan_now` → **Appeler le service**

**Dans une automation :**

```yaml
# Scan hebdomadaire le lundi à 3h du matin
automation:
  - alias: "Scan médiathèque hebdomadaire"
    trigger:
      - platform: time
        at: "03:00:00"
    condition:
      - condition: time
        weekday:
          - mon
    action:
      - service: media_gap_analyzer.scan_now
```

**Notification quand il manque des films :**

```yaml
automation:
  - alias: "Alerte films manquants"
    trigger:
      - platform: state
        entity_id: sensor.films_manquants
    condition:
      - condition: numeric_state
        entity_id: sensor.films_manquants
        above: 0
    action:
      - service: notify.mobile_app_mon_telephone
        data:
          title: "🎬 Médiathèque incomplète"
          message: >
            Il manque {{ states('sensor.films_manquants') }} film(s)
            dans vos collections !
```

---

## 🔍 Comment ça marche

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│  Vos dossiers   │────▶│   Scanner    │────▶│  Analyseur  │
│  films/séries   │     │  (parsing    │     │  (compare   │
│  /anime         │     │   noms)      │     │  avec TMDb) │
└─────────────────┘     └──────────────┘     └──────┬──────┘
                                                     │
                                                     ▼
                                             ┌──────────────┐
                                             │   Sensors    │
                                             │  Home Asst.  │
                                             └──────────────┘
```

1. **Scanner** — Parcourt vos dossiers et extrait le nom/année des films et le pattern S01E01 des épisodes
2. **TMDb** — Recherche chaque film/série sur TMDb pour identifier les collections (trilogies, sagas) et la liste complète des épisodes
3. **Analyse** — Compare ce que vous avez vs ce qui existe → identifie les manques
4. **Sensors** — Expose les résultats dans Home Assistant

---

## ❓ FAQ

**Q : Combien de temps dure un scan ?**  
A : Ça dépend de la taille de votre médiathèque. Le scan de fichiers est rapide, mais les appels TMDb sont limités à ~40 requêtes/10s. Pour 100 films, comptez ~2 minutes.

**Q : Faut-il payer pour TMDb ?**  
A : Non, la clé API est gratuite pour un usage personnel.

**Q : Mes films sont sur un NAS, comment faire ?**  
A : Montez votre partage réseau dans HA. Par exemple via `/etc/fstab` :
```
//192.168.1.100/films /media/films cifs username=xxx,password=xxx 0 0
```
Ou utilisez le add-on **Samba share** de HA.

**Q : Le scan ne trouve pas mes films/séries ?**  
A : Vérifiez que :
- Le chemin est accessible depuis HA (testez avec `ls /media/films` en SSH)
- Les noms de fichiers contiennent le nom du film et idéalement l'année : `Inception (2010).mkv`
- Les épisodes contiennent le pattern `S01E01` dans le nom du fichier

**Q : Il détecte des films "manquants" que je ne veux pas ?**  
A : C'est normal — TMDb liste tous les films d'une collection, y compris les spin-offs. Une future version permettra d'ignorer certains titres.

---

## 🤝 Contribuer

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une [issue](https://github.com/Turiko313/HA-Suivi-mediatheque/issues) ou une pull request.

## 📄 Licence

MIT