
# Bot de Suivi Spotify 🎧

Ce programme est un bot automatisé pour suivre des utilisateurs Spotify, avec une interface graphique en Python. Les utilisateurs suivis sont stockés dans une base de données SQLite locale.

---

## 🛠 Prérequis

### 1. Python
- Python 3.9 ou version ultérieure est requis.  
[Télécharger Python](https://www.python.org/downloads/)

### 2. Bibliothèques Python nécessaires

Installez les bibliothèques avec :

```bash
pip install selenium customtkinter pystray pillow webdriver-manager
```

> Sous Linux, vous devrez peut-être installer `tkinter` :
> ```bash
> sudo apt install python3-tk
> ```

### 3. Chrome & ChromeDriver Automatique

- Google Chrome doit être installé : [Télécharger Chrome](https://www.google.com/chrome/)
- Grâce à `webdriver-manager`, ChromeDriver est géré automatiquement, aucun téléchargement manuel requis.

Assurez-vous que ce code est utilisé :

```python
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
```

---

## 🚀 Lancement du Programme

Dans le terminal, exécutez :

```bash
python Spotify_Follow_Bot.py
```

---

## 🧾 Utilisation

1. Entrez vos identifiants Spotify.
2. Indiquez l'ID utilisateur cible.
3. Configurez les limites et délais.
4. Cliquez sur “Démarrer” pour lancer le bot.

---

## 💾 Gestion des Données

- Les utilisateurs suivis sont stockés dans `followed_users.db`.
- Les paramètres sont enregistrés dans `settings.json`.
- Les préférences de thème et langue sont dans `themes.json` et `lang/*.json`.

---

## 👨‍💻 Développeur

- Infos du développeur visibles dans l’onglet “Producteur” de l’application.
- Lien GitHub accessible directement depuis l’interface.

---

## ⚠️ Avertissement

Ce bot peut violer les conditions d'utilisation de Spotify. Utilisez-le à vos propres risques.

---
