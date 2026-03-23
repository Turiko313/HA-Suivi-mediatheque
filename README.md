# 🎬 Suivi Médiathèque pour Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/Turiko313/HA-Suivi-mediatheque)](https://github.com/Turiko313/HA-Suivi-mediatheque/releases)

> Vous avez le 1 et le 3 d'une trilogie mais pas le 2 ?  
> Il vous manque des épisodes dans une série, un anime ou un dessin animé ?  
> **Suivi Médiathèque** scanne vos disques et vous dit exactement ce qu'il manque.

---

## ✨ Fonctionnalités

| | Fonctionnalité |
|---|---|
| 🎥 | **Films** — Détecte les volets manquants dans les sagas et trilogies (TMDb ou Wikidata) |
| 📺 | **Séries TV** — Repère les épisodes et saisons manquants |
| 🎌 | **Anime** — Idem, avec un chemin et un sensor dédiés |
| 🧸 | **Dessins animés** — Catégorie séparée pour les dessins animés |
| 🔑 | **TMDb optionnel** — Fonctionne aussi sans clé API (Wikidata pour les films, détection locale pour les épisodes) |
| 📂 | **Détection auto des chemins** — Menu déroulant qui liste les stockages configurés dans HA + saisie manuelle |
| 🔄 | **Scan planifié** — Analyse automatique configurable (toutes les heures, jours, semaines…) |
| ▶️ | **Scan manuel** — Service `media_gap_analyzer.scan_now` pour lancer un scan immédiat |
| 📊 | **Sensors HA** — Nombre d'éléments manquants + détails complets dans les attributs |
| 💾 | **Multi-chemins** — Scannez plusieurs disques ou partages NAS |
| 🖥️ | **Config UI** — Configuration 100% via l'interface Home Assistant |
| 📦 | **HACS** — Installation en un clic via dépôt personnalisé |

---

## 📋 Pré-requis

1. **Home Assistant** 2024.1.0 ou supérieur
2. **Clé API TMDb** *(optionnelle)* — Créez un compte sur [themoviedb.org](https://www.themoviedb.org/) puis rendez-vous dans *Paramètres → API* pour obtenir votre clé v3. Sans cette clé, l'intégration utilise **Wikidata** (gratuit, sans inscription) pour détecter les films manquants dans les collections, et la détection locale des trous dans la numérotation pour les épisodes.
3. **Médiathèque accessible** — Vos fichiers doivent être accessibles depuis HA, soit via un NAS (l'intégration se connecte directement en SMB/CIFS), soit via des dossiers montés localement (`/media/`, etc.)

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
| **Clé API TMDb** *(optionnel)* | Votre clé API v3 (laissez vide pour le mode local) | `a1b2c3d4e5f6...` |
| **Langue** | Langue des résultats TMDb | `fr` |
| **Intervalle de scan** | En heures (1 à 720) | `24` (1 fois/jour) ou `168` (1 fois/semaine) |
| **Adresse du NAS** *(optionnel)* | IP ou nom d'hôte de votre NAS | `192.168.1.100` |
| **Utilisateur NAS** *(optionnel)* | Identifiant SMB/CIFS | `monuser` |
| **Mot de passe NAS** *(optionnel)* | Mot de passe SMB/CIFS | `monpass` |
| **Chemins des films** | Menu déroulant + saisie libre | `/media/Films` |
| **Chemins des séries** | Menu déroulant + saisie libre | `/media/Series` |
| **Chemins des animés** | Menu déroulant + saisie libre | `/media/Anime` |
| **Chemins des dessins animés** | Menu déroulant + saisie libre | `/media/Dessins_animes` |

> 💡 **Stockage externe configuré ?** Les chemins détectés dans `/media/` et `/share/` apparaissent automatiquement dans les menus déroulants.  
> 💡 **Chemin personnalisé ?** Vous pouvez aussi taper un chemin manuellement dans le champ.  
> 💡 **NAS configuré ?** Entrez le nom du partage (ex : `Films`). L'intégration se connecte directement en SMB.  
> 💡 **Plusieurs chemins ?** Vous pouvez sélectionner plusieurs chemins dans chaque menu déroulant.

### Mode avec TMDb vs mode local

| | Avec TMDb | Sans TMDb (Wikidata) |
|---|---|---|
| **Films** | ✅ Détecte les films manquants dans les collections/sagas via TMDb | ✅ Détecte les films manquants via Wikidata (gratuit, sans clé API) |
| **Séries / Anime / Dessins animés** | ✅ Compare avec la liste complète des épisodes TMDb | ✅ Détecte les trous dans la numérotation (ex : a E01 et E03 → manque E02) |

> 💡 **Wikidata** est une base de données libre et gratuite maintenue par la communauté Wikimedia. L'intégration l'utilise automatiquement quand aucune clé TMDb n'est configurée pour identifier les sagas/trilogies et leurs volets manquants.

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

### Séries / Anime / Dessins animés

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
| **Épisodes manquants (Dessins animés)** | Nombre d'épisodes manquants | Liste groupée par dessin animé et saison |
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

### Avec clé TMDb

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│  Vos dossiers   │────▶│   Scanner    │────▶│  Analyseur  │
│  films/séries   │     │  (parsing    │     │  (compare   │
│  /anime/dessins │     │   noms)      │     │  avec TMDb) │
└─────────────────┘     └──────────────┘     └──────┬──────┘
                                                     │
                                                     ▼
                                             ┌──────────────┐
                                             │   Sensors    │
                                             │  Home Asst.  │
                                             └──────────────┘
```

### Sans clé TMDb (mode Wikidata + local)

```
┌─────────────────┐     ┌──────────────┐     ┌──────────────────┐
│  Vos dossiers   │────▶│   Scanner    │────▶│  Films :         │
│  films/séries   │     │  (parsing    │     │  Wikidata (P179) │
│  /anime/dessins │     │   noms)      │     │                  │
└─────────────────┘     └──────────────┘     │  Séries/Anime :  │
                                              │  Détection locale│
                                              │  (trous numérot.)│
                                              └────────┬─────────┘
                                                       │
                                                       ▼
                                              ┌──────────────┐
                                              │   Sensors    │
                                              │  Home Asst.  │
                                              └──────────────┘
```

1. **Scanner** — Parcourt vos dossiers et extrait le nom/année des films et le pattern S01E01 des épisodes
2. **Analyse TMDb** *(si clé configurée)* — Recherche chaque film/série sur TMDb pour identifier les collections et la liste complète des épisodes
3. **Analyse Wikidata** *(si pas de clé TMDb, pour les films)* — Recherche chaque film sur Wikidata, identifie la saga via la propriété P179 (« fait partie de la série »), puis récupère tous les volets via SPARQL
4. **Analyse locale** *(si pas de clé TMDb, pour les séries)* — Détecte les trous dans la numérotation des épisodes (a E01 et E03 → manque E02)
5. **Sensors** — Expose les résultats dans Home Assistant

---

## ❓ FAQ

**Q : Combien de temps dure un scan ?**  
A : Ça dépend de la taille de votre médiathèque. Le scan de fichiers est rapide, mais les appels TMDb sont limités à ~40 requêtes/10s. Pour 100 films, comptez ~2 minutes. Sans TMDb, le scan est quasi instantané.

**Q : Faut-il payer pour TMDb ?**  
A : Non, la clé API est gratuite pour un usage personnel. Et elle est désormais optionnelle !

**Q : Quelle est la différence entre "animés" et "dessins animés" ?**  
A : Ce sont deux catégories séparées avec chacune leur propre chemin et sensor. « Animés » est destiné aux anime japonais, « Dessins animés » aux dessins animés occidentaux (Disney, Pixar, etc.).

**Q : Mes films sont sur un NAS, comment faire ?**  
A : **Trois options, de la plus simple à la plus avancée :**

#### Option 1 — Connexion directe via l'intégration (recommandé) ✅

L'intégration se connecte directement à votre NAS en SMB/CIFS, **sans aucun montage à faire**.

Dans la configuration de Suivi Médiathèque :
- **Adresse du NAS** : `192.168.1.100` (l'IP de votre NAS)
- **Utilisateur NAS** : votre identifiant SMB (celui de votre Synology, QNAP, etc.)
- **Mot de passe NAS** : votre mot de passe SMB
- **Chemins** : le nom du partage, ex : `Films`, `Series`, `Anime`, `Dessins_animes`

```
Exemple avec un Synology qui partage les dossiers "Films", "Series", "Anime" et "Dessins_animes" :
  → Adresse NAS : 192.168.1.50
  → Utilisateur : mediacenter
  → Mot de passe : monmotdepasse
  → Chemins films : Films
  → Chemins séries : Series
  → Chemins anime : Anime
  → Chemins dessins animés : Dessins_animes
```

> ⚠️ **L'add-on "Samba Share" de HA** sert à partager les fichiers de HA *vers* votre réseau (pour éditer `configuration.yaml` depuis votre PC). Ce n'est **pas** ce qu'il faut pour accéder à votre NAS.

#### Option 2 — Stockage réseau HA (HAOS uniquement) 🔽

Si vous utilisez Home Assistant OS :
1. **Paramètres** → **Système** → **Stockage** → **Ajouter un stockage réseau**
2. Renseignez IP, partage, identifiants, et choisissez le type **Média**
3. Le partage sera monté dans `/media/`
4. Dans Suivi Médiathèque, **les chemins apparaissent automatiquement dans les menus déroulants** ! Il suffit de les sélectionner.

#### Option 3 — Montage manuel (`/etc/fstab`)

Pour les installations Docker ou Supervised :
```bash
# Exemple pour monter un partage CIFS dans /media/films
sudo mkdir -p /media/films
echo '//192.168.1.100/Films /media/films cifs username=user,password=pass,uid=1000 0 0' | sudo tee -a /etc/fstab
sudo mount -a
```
Puis dans Suivi Médiathèque, sélectionnez le chemin `/media/films` dans le menu déroulant.

**Q : Le scan ne trouve pas mes films/séries ?**  
A : Vérifiez que :
- Le chemin est accessible depuis HA (testez avec `ls /media/films` en SSH)
- Les noms de fichiers contiennent le nom du film et idéalement l'année : `Inception (2010).mkv`
- Les épisodes contiennent le pattern `S01E01` dans le nom du fichier

**Q : Il détecte des films "manquants" que je ne veux pas ?**  
A : C'est normal — TMDb/Wikidata listent tous les films d'une collection, y compris les spin-offs. Une future version permettra d'ignorer certains titres.

**Q : Qu'est-ce que Wikidata ?**  
A : [Wikidata](https://www.wikidata.org/) est une base de données libre et gratuite maintenue par la communauté Wikimedia (les mêmes qui font Wikipédia). L'intégration l'utilise comme alternative gratuite à TMDb pour identifier les sagas de films et leurs volets manquants. Aucune inscription ni clé API n'est nécessaire.

**Q : TMDb ou Wikidata, lequel est le mieux ?**  
A : TMDb est plus complet et plus rapide pour les films (toutes les collections sont bien référencées). Wikidata est gratuit et sans inscription, mais la couverture des franchises peut être moins exhaustive. Si vous avez une grande médiathèque, nous recommandons de créer une clé TMDb gratuite.

---

## 🤝 Contribuer

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une [issue](https://github.com/Turiko313/HA-Suivi-mediatheque/issues) ou une pull request.

## 📄 Licence

MIT