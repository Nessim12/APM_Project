# APM Project - Guide d'installation rapide (Docker & Django)

Ce projet utilise **Docker** et **Docker Compose** pour simplifier la configuration de l'environnement de développement local avec **Django** et **MariaDB**.

Les fichiers téléversés sont gérés séparément des métadonnées: les enregistrements restent dans PostgreSQL/Supabase, tandis que les binaires (PDF, PNG, DOCX, etc.) peuvent être stockés dans un bucket Supabase Storage quand l'environnement est configuré pour le faire.

---

## 📋 Prérequis

Avant de commencer, assurez-vous d'avoir installé les outils suivants sur votre machine :

1. **Git** (pour cloner le projet).
2. **Docker Desktop** (assurez-vous qu'il est démarré et que le moteur Docker est actif - icône verte).

---

## 🚀 Étape 1 : Récupérer le projet

Clonez le dépôt Git du projet (remplacez le lien ci-dessous par l'URL de votre dépôt) :
```bash
git clone <URL_DU_DEPOT_GIT>
cd APM-Project
```

---

## 🛠️ Étape 2 : Construire les images Docker

Depuis la racine du projet (là où se trouve le fichier `docker-compose.yml`), exécutez la commande suivante pour télécharger les images nécessaires et construire le conteneur Django :
```bash
docker compose build
```

Si vous activez Supabase Storage pour les documents, ajoutez les variables d'environnement suivantes au conteneur Django:

- `SUPABASE_STORAGE_ENABLED=true`
- `SUPABASE_STORAGE_BUCKET=<nom-du-bucket>`
- `SUPABASE_STORAGE_ACCESS_KEY=<access-key>`
- `SUPABASE_STORAGE_SECRET_KEY=<secret-key>`
- `SUPABASE_STORAGE_ENDPOINT=https://<project-ref>.supabase.co/storage/v1/s3`
- `SUPABASE_STORAGE_REGION=eu-central-1`

---

## 🗄️ Étape 3 : Appliquer les migrations de base de données

Une fois la construction terminée, appliquez les migrations Django pour initialiser les tables de la base de données MariaDB :
```bash
docker compose run --rm web python manage.py migrate
```

---

## 🏃‍♂️ Étape 4 : Lancer le projet

Démarrez les services (Base de données + Django) en arrière-plan :
```bash
docker compose up -d
```

---

## 🌍 Étape 5 : Accéder à l'application

Ouvrez votre navigateur et accédez à l'adresse suivante :
- **Django :** [http://localhost:8000](http://localhost:8000)

---

## 🛑 Commandes utiles

- **Arrêter le projet :**
  ```bash
  docker compose down
  ```
- **Voir les logs des conteneurs en temps réel :**
  ```bash
  docker compose logs -f
  ```
- **Accéder au shell de Django :**
  ```bash
  docker compose run --rm web python manage.py shell
  ```
- **Créer un superutilisateur Django :**
  ```bash
  docker compose run --rm web python manage.py createsuperuser
  ```
