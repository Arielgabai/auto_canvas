## Auto Canvas - Traitement images automatique (3x3 par page)

### Prérequis
- Python 3.12 recommandé
- wkhtmltopdf installé (Windows): `C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe`
- Compte API PhotoRoom (clé API)

### Installation
1. Créer et activer un venv (Windows PowerShell):
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
2. Installer les dépendances:
```
pip install -r requirements.txt
```

3. Créer un fichier `.env` à la racine:
```
PHOTOROOM_API_KEY=sk_xxx  # Clé API PhotoRoom (obligatoire)
WKHTMLTOPDF_PATH=C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe
INPUT_DIR=C:\\Users\\agabai\\OneDrive - Trimane\\Bureau\\auto_canvas\\drive_in  # Dossier du Drive à surveiller
OUTPUT_PDF_DIR=C:\\Users\\agabai\\OneDrive - Trimane\\Bureau\\auto_canvas\\drive_out
WORK_NO_BG_DIR=C:\\Users\\agabai\\OneDrive - Trimane\\Bureau\\auto_canvas\\work\\no_bg
WORK_SHADOW_DIR=C:\\Users\\agabai\\OneDrive - Trimane\\Bureau\\auto_canvas\\work\\shadow
STATE_FILE=C:\\Users\\agabai\\OneDrive - Trimane\\Bureau\\auto_canvas\\.state.json
```

Créer les dossiers si besoin: `drive_in`, `drive_out`, `work\no_bg`, `work\shadow`.

### Utilisation
- Lancer le watcher (surveille `INPUT_DIR` et traite par batchs de 9 images):
```
python -m auto_canvas.watch
```

- Traitement manuel d'un batch de 9 (prend les 9 premières images de `INPUT_DIR`):
```
python -m auto_canvas.pipeline --once
```

- Traitement manuel en listant explicitement des chemins d'images:
```
python -m auto_canvas.pipeline --paths "C:\\path\\to\\img1.jpg" "C:\\path\\to\\img2.jpg" ...
```

### Google Drive (Cloud)
- Variables d'environnement requises:
  - `GDRIVE_SERVICE_ACCOUNT_JSON`: chemin du fichier JSON de compte de service (monter via secret Render)
  - `GDRIVE_INPUT_FOLDER_ID`: ID du dossier Drive à surveiller (entrées)
  - `GDRIVE_OUTPUT_FOLDER_ID`: ID du dossier Drive où uploader les PDF

- Lancer le watcher Drive (local):
```
python -m auto_canvas.watch_gdrive
```

### Déploiement Render
1. Pousser sur GitHub
2. Créer un service Web sur Render (Docker)
3. Renseigner les env vars: `PHOTOROOM_API_KEY`, `WKHTMLTOPDF_PATH=/usr/local/bin/wkhtmltopdf`, `GDRIVE_SERVICE_ACCOUNT_JSON=/opt/secrets/sa.json`, `GDRIVE_INPUT_FOLDER_ID`, `GDRIVE_OUTPUT_FOLDER_ID`, etc.
4. Ajouter le secret file `sa.json` dans Render (Secret Files) et le monter à `/opt/secrets/sa.json`.
5. Le service démarre et: 
   - si `GDRIVE_INPUT_FOLDER_ID` est défini, utilise `watch_gdrive`
   - sinon, utilise le watcher local `watch` (dossiers `/app/drive_in` et `/app/drive_out`).

### Fonctionnement
- Watcher détecte les nouvelles images dans `INPUT_DIR`
- Quand 9 nouvelles images sont stables, pipeline:
  - supprime le fond via PhotoRoom
  - ajoute une ombre (Pillow)
  - génère un PDF 3x3 via wkhtmltopdf dans `OUTPUT_PDF_DIR`
- Les PDF sont nommés par timestamp.

### Dépannage
- wkhtmltopdf introuvable: vérifier `WKHTMLTOPDF_PATH` dans `.env`
- API 401: vérifier `PHOTOROOM_API_KEY`
- Images verrouillées par OneDrive: le watcher attend que le fichier soit stable (taille inchangée)

### Test rapide (sans API)
Si vous avez déjà des images avec ombre dans `work/shadow`, vous pouvez générer un PDF directement:
```
python -m auto_canvas.smoke
```


