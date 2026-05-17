# 📈 Tableau de bord BRVM

Application web d'analyse et de suivi de la Bourse Régionale des Valeurs Mobilières (BRVM).

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-239120?style=for-the-badge&logo=plotly&logoColor=white)

---

## 🚀 Fonctionnalités

| Fonctionnalité | Description |
|----------------|-------------|
| 🏆 **Top 5 / Flop 5** | Meilleures et pires performances quotidiennes |
| 📊 **Analyse individuelle** | Cours, volume, historique complet |
| 📈 **Moyennes mobiles** | MM20 et MM50 pour identifier les tendances |
| 📉 **RSI** | Relative Strength Index (sur-achat/sur-vente) |
| 📊 **Bandes de Bollinger** | Analyse de la volatilité et détection de squeezes |
| 🔍 **Comparaison multi-valeurs** | Comparez jusqu'à 4 valeurs simultanément |
| 🔔 **Alertes personnalisées** | Seuils de prix et variations quotidiens |
| 🏛️ **Synthèse du marché** | Transactions, capitalisations, indices BRVM |

---

## 🛠️ Technologies utilisées

- **[Streamlit](https://streamlit.io/)** : Framework pour l'interface utilisateur
- **[Pandas](https://pandas.pydata.org/)** : Manipulation et analyse des données
- **[Plotly](https://plotly.com/)** : Graphiques interactifs
- **[BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/)** : Scraping des données
- **[Requests](https://docs.python-requests.org/)** : Requêtes HTTP

---

## 📦 Installation locale

Pour exécuter l'application sur votre machine :

```bash
# 1. Cloner le dépôt
git clone https://github.com/spoudar/brvm-dashboard.git
cd brvm-dashboard

# 2. Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Sur Windows : venv\Scripts\activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Lancer l'application
streamlit run brvm_dashboard.py
