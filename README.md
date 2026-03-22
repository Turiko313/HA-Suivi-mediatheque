# Media Gap Analyzer pour Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Integration Home Assistant qui analyse votre mediatheque et detecte les films et episodes manquants dans vos collections, series et animes.

## Fonctionnalites

- **Films** : detecte les films manquants dans les sagas/trilogies (ex: il vous manque le 2e volet du Seigneur des Anneaux)
- **Series** : detecte les episodes manquants dans vos series TV
- **Anime** : idem pour vos animes
- **Scan planifie** : analyse automatique selon un intervalle configurable (toutes les 6h, 24h, hebdomadaire...)
- **Scan manuel** : service `media_gap_analyzer.scan_now` declenchable depuis une automation ou le panneau developpeur
- **Sensors HA** : entites avec le nombre d'elements manquants + details dans les attributs
- **Multi-chemins** : scannez plusieurs disques/NAS (chemins separes par des virgules)
- **Interface UI** : configuration complete via l'interface HA (Config Flow)
- **Compatible HACS**

## Pre-requis

1. **Cle API TMDb gratuite** : creez un compte sur [themoviedb.org](https://www.themoviedb.org/) puis allez dans *Parametres > API* pour obtenir votre cle (v3 auth).
2. **Disques reseaux montes** : vos NAS/partages doivent etre montes comme dossiers locaux dans HA (via `/etc/fstab`, le add-on Samba, ou montage dans `/media/`).

## Installation

### Via HACS (recommande)

1. Ouvrez HACS dans Home Assistant
2. Cliquez sur les 3 points > *Depots personnalises*
3. Ajoutez `https://github.com/Turiko313/HA-Suivi-mediatheque` en categorie *Integration*
4. Cherchez "Media Gap Analyzer" et installez
5. Redemarrez Home Assistant

### Installation manuelle

1. Copiez le dossier `custom_components/media_gap_analyzer/` dans votre dossier `config/custom_components/`
2. Redemarrez Home Assistant

## Configuration

1. Allez dans *Parametres > Appareils et services > Ajouter une integration*
2. Cherchez "Media Gap Analyzer"
3. Renseignez :
   - **Cle API TMDb** : votre cle API v3
   - **Langue** : langue pour les noms de films/series (fr par defaut)
   - **Intervalle de scan** : en heures (24 par defaut)
   - **Chemins des films** : ex. `/media/films` ou `/mnt/nas/movies,/media/films`
   - **Chemins des series** : ex. `/media/series`
   - **Chemins des animes** : ex. `/media/anime`

## Organisation attendue de la mediatheque

### Films

`
/media/films/
+-- Inception (2010)/
|   +-- Inception.mkv
+-- The Matrix (1999).mkv
+-- Le.Seigneur.des.Anneaux.La.Communaute.de.l.Anneau.2001.1080p.mkv
`

Chaque film peut etre :
- Un fichier video directement dans le dossier
- Un sous-dossier contenant le fichier video

### Series / Anime

`
/media/series/
+-- Breaking Bad/
|   +-- Season 01/
|   |   +-- S01E01 - Pilot.mkv
|   |   +-- S01E02 - Cat's in the Bag.mkv
|   +-- Season 02/
|       +-- S02E01.mkv
+-- The Office/
    +-- S01E01.mkv
    +-- S01E02.mkv
`

Les fichiers doivent contenir le pattern `S01E01` (ou `1x01`) dans leur nom.

## Sensors crees

| Sensor | Description |
|--------|-------------|
| `sensor.films_manquants` | Nombre de films manquants. Attributs : detail par collection. |
| `sensor.episodes_manquants_series` | Nombre d'episodes manquants. Attributs : detail par serie/saison. |
| `sensor.episodes_manquants_anime` | Idem pour les animes. |
| `sensor.dernier_scan_mediatheque` | Horodatage du dernier scan + statistiques. |

### Exemple d'attributs du sensor Films manquants

`yaml
missing_by_collection:
  The Lord of the Rings Collection:
    - "The Lord of the Rings: The Two Towers (2002)"
  The Matrix Collection:
    - "The Matrix Reloaded (2003)"
total_missing: 2
scanned: 45
collections_found: 8
`

## Service

### `media_gap_analyzer.scan_now`

Lance un scan immediat. Utilisable dans les automations :

`yaml
automation:
  - alias: "Scan mediatheque hebdomadaire"
    trigger:
      - platform: time
        at: "03:00:00"
    condition:
      - condition: time
        weekday:
          - mon
    action:
      - service: media_gap_analyzer.scan_now
`

## Modifier les options apres installation

*Parametres > Appareils et services > Media Gap Analyzer > Configurer*

Vous pouvez modifier l'intervalle de scan et les chemins a tout moment.

## Licence

MIT
