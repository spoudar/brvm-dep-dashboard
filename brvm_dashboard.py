import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import re

# ========== GESTION DES ALERTES ==========
FICHIER_ALERTES = "alertes_brvm.json"

def charger_alertes():
    """Charge les alertes depuis le fichier JSON"""
    if os.path.exists(FICHIER_ALERTES):
        with open(FICHIER_ALERTES, 'r') as f:
            return json.load(f)
    return {}

def sauvegarder_alertes(alertes):
    """Sauvegarde les alertes dans le fichier JSON"""
    with open(FICHIER_ALERTES, 'w') as f:
        json.dump(alertes, f, indent=4)

def verifier_alertes(alertes, ticker, prix_actuel, variation_quotidienne):
    """Vérifie si une alerte est déclenchée pour un ticker donné"""
    if ticker not in alertes:
        return None
    
    alertes_declenchees = []
    regles = alertes[ticker]
    
    # Vérification seuil haut
    if "seuil_haut" in regles and prix_actuel >= regles["seuil_haut"]:
        alertes_declenchees.append(f"📈 **{ticker}** a atteint son seuil haut : {prix_actuel:,.0f} FCFA (≥ {regles['seuil_haut']:,.0f})")
    
    # Vérification seuil bas
    if "seuil_bas" in regles and prix_actuel <= regles["seuil_bas"]:
        alertes_declenchees.append(f"📉 **{ticker}** a atteint son seuil bas : {prix_actuel:,.0f} FCFA (≤ {regles['seuil_bas']:,.0f})")
    
    # Vérification variation hausse
    if "variation_hausse" in regles and variation_quotidienne >= regles["variation_hausse"]:
        alertes_declenchees.append(f"🚀 **{ticker}** a augmenté de {variation_quotidienne:.1f}% (seuil: ≥ {regles['variation_hausse']}%)")
    
    # Vérification variation baisse
    if "variation_baisse" in regles and variation_quotidienne <= regles["variation_baisse"]:
        alertes_declenchees.append(f"📉 **{ticker}** a baissé de {variation_quotidienne:.1f}% (seuil: ≤ {regles['variation_baisse']}%)")
    
    return alertes_declenchees if alertes_declenchees else None

# Configuration de la page
st.set_page_config(page_title="BRVM Dashboard", layout="wide")

# ========== EN-TÊTE PERSONNALISÉ ==========
st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <h1>🏦 Tableau de bord BRVM</h1>
        <p style="color: #666;">Analyse et suivi des marchés financiers ouest-africains (la bourse d'abidjan)</p>
    </div>
""", unsafe_allow_html=True)
st.markdown("---")
# ========== 1. LISTE DES TICKERS (définie au tout début) ==========
tickers_brvm = [
    "ABJC", "BICB", "BICC", "BNBC", "BOAB", "BOABF", "BOAC", "BOAM", 
    "BOAN", "BOAS", "CABC", "CBIBF", "CFAC", "CIEC", "ECOC", "ETIT", 
    "FTSC", "LNBB", "NEIC", "NSBC", "NTLC", "ONTBF", "ORAC", "ORGT", 
    "PALC", "PRSC", "SAFC", "SCRC", "SDCC", "SDSC", "SEMC", "SGBC", 
    "SHEC", "SIBC", "SICC", "SIVC", "SLBC", "SMBC", "SNTS", "SOGC", 
    "SPHC", "STAC", "STBC", "TTLC", "TTLS", "UNLC", "UNXC"
]

# ========== 2. FONCTION DE CHARGEMENT (utilisée partout) ==========
@st.cache_data
def charger_donnees(ticker):
    url = f"https://raw.githubusercontent.com/Fredysessie/brvm-data-public/main/data/{ticker}/{ticker}.daily.csv"
    try:
        df = pd.read_csv(url)
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    except:
        return None

st.success("✅ Streamlit est bien lancé !")

# ========== ALERTES DANS LA BARRE LATÉRALE ==========
with st.sidebar:
    st.header("🔔 Gestion des alertes")
    
    # Charger les alertes existantes
    alertes = charger_alertes()
    
    # Onglets pour créer et voir les alertes
    tab_creer, tab_voir = st.tabs(["➕ Créer une alerte", "📋 Mes alertes"])
    
    with tab_creer:
        st.subheader("Nouvelle alerte")
        
        # Sélection de la valeur
        ticker_alerte = st.selectbox(
            "Choisissez une valeur",
            tickers_brvm,
            key="ticker_alerte"
        )
        
        # Type d'alerte
        type_alerte = st.radio(
            "Type d'alerte",
            ["Seuil de prix", "Variation quotidienne", "Les deux"]
        )
        
        nouvelles_regles = {}
        
        if type_alerte in ["Seuil de prix", "Les deux"]:
            col_seuil1, col_seuil2 = st.columns(2)
            with col_seuil1:
                seuil_haut = st.number_input(
                    "Seuil haut (FCFA)",
                    min_value=0,
                    value=5000,
                    step=500,
                    key="seuil_haut"
                )
                if seuil_haut > 0:
                    nouvelles_regles["seuil_haut"] = seuil_haut
            
            with col_seuil2:
                seuil_bas = st.number_input(
                    "Seuil bas (FCFA)",
                    min_value=0,
                    value=1000,
                    step=500,
                    key="seuil_bas"
                )
                if seuil_bas > 0:
                    nouvelles_regles["seuil_bas"] = seuil_bas
        
        if type_alerte in ["Variation quotidienne", "Les deux"]:
            col_var1, col_var2 = st.columns(2)
            with col_var1:
                variation_hausse = st.number_input(
                    "Alerte hausse (%)",
                    min_value=0,
                    value=5,
                    step=1,
                    key="var_hausse"
                )
                if variation_hausse > 0:
                    nouvelles_regles["variation_hausse"] = variation_hausse
            
            with col_var2:
                variation_baisse = st.number_input(
                    "Alerte baisse (%)",
                    max_value=0,
                    value=-5,
                    step=1,
                    key="var_baisse"
                )
                if variation_baisse < 0:
                    nouvelles_regles["variation_baisse"] = variation_baisse
        
        if nouvelles_regles:
            if st.button("💾 Sauvegarder l'alerte", key="btn_sauvegarder"):
                alertes[ticker_alerte] = nouvelles_regles
                sauvegarder_alertes(alertes)
                st.success(f"✅ Alerte enregistrée pour {ticker_alerte}")
                st.rerun()
    
    with tab_voir:
        if alertes:
            for ticker, regles in alertes.items():
                with st.expander(f"📌 {ticker}"):
                    if "seuil_haut" in regles:
                        st.write(f"📈 Seuil haut : {regles['seuil_haut']:,.0f} FCFA")
                    if "seuil_bas" in regles:
                        st.write(f"📉 Seuil bas : {regles['seuil_bas']:,.0f} FCFA")
                    if "variation_hausse" in regles:
                        st.write(f"🚀 Variation hausse : ≥ {regles['variation_hausse']}%")
                    if "variation_baisse" in regles:
                        st.write(f"📉 Variation baisse : ≤ {regles['variation_baisse']}%")
                    
                    if st.button(f"🗑️ Supprimer", key=f"del_{ticker}"):
                        del alertes[ticker]
                        sauvegarder_alertes(alertes)
                        st.rerun()
        else:
            st.info("Aucune alerte enregistrée")

# ========== 3. TOP 5 ET FLOP 5 ==========
st.markdown("---")
st.subheader("🏆 Performance du jour")

@st.cache_data
def get_performance_quotidienne():
    performances = []
    for ticker in tickers_brvm:
        df = charger_donnees(ticker)
        if df is not None and len(df) >= 2:
            dernier = df.iloc[-1]
            precedent = df.iloc[-2]
            variation_pct = ((dernier['Close'] - precedent['Close']) / precedent['Close']) * 100
            performances.append({
                "Ticker": ticker,
                "Cours (FCFA)": dernier['Close'],
                "Variation (%)": round(variation_pct, 2),
                "Volume": dernier['Volume']
            })
    return pd.DataFrame(performances)

df_perf = get_performance_quotidienne()

if not df_perf.empty:
    df_top5 = df_perf.nlargest(5, "Variation (%)")
    df_flop5 = df_perf.nsmallest(5, "Variation (%)")
    
    col_top, col_flop = st.columns(2)
    
    with col_top:
        st.markdown("#### 📈 Top 5 hausses")
        st.dataframe(
            df_top5[["Ticker", "Cours (FCFA)", "Variation (%)", "Volume"]],
            hide_index=True,
            column_config={
                "Variation (%)": st.column_config.NumberColumn("Variation (%)", format="%.2f %%"),
                "Cours (FCFA)": st.column_config.NumberColumn("Cours (FCFA)", format="%.0f")
            }
        )
    
    with col_flop:
        st.markdown("#### 📉 Top 5 baisses")
        st.dataframe(
            df_flop5[["Ticker", "Cours (FCFA)", "Variation (%)", "Volume"]],
            hide_index=True,
            column_config={
                "Variation (%)": st.column_config.NumberColumn("Variation (%)", format="%.2f %%"),
                "Cours (FCFA)": st.column_config.NumberColumn("Cours (FCFA)", format="%.0f")
            }
        )
    
    meilleur = df_top5.iloc[0]
    pire = df_flop5.iloc[0]
    st.info(f"📌 **Meilleure performance** : {meilleur['Ticker']} ({meilleur['Variation (%)']}%) | **Moins bonne** : {pire['Ticker']} ({pire['Variation (%)']}%)")
else:
    st.warning("Impossible de calculer les performances du jour pour le moment")

st.markdown("---")

 # ========== 4. ANALYSE INDIVIDUELLE (reste du code original) ==========
selected = st.selectbox("Choisissez une valeur pour une analyse détaillée", tickers_brvm)

df = charger_donnees(selected)

if df is not None and not df.empty:
    dernier = df.iloc[-1]
    col1, col2, col3 = st.columns(3)
        # Calcul de la variation quotidienne en pourcentage
    if len(df) >= 2:
        precedent = df.iloc[-2]
        variation_pct = ((dernier['Close'] - precedent['Close']) / precedent['Close']) * 100
    else:
        variation_pct = 0
    
    # Vérification des alertes
    alertes = charger_alertes()
    alertes_declenchees = verifier_alertes(alertes, selected, dernier['Close'], variation_pct)
    
    if alertes_declenchees:
        with st.container():
            st.warning("🔔 **Alertes déclenchées**")
            for alerte in alertes_declenchees:
                st.write(alerte)
        # Affichage des métriques avec couleurs
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Dernier cours", f"{dernier['Close']:,.0f} FCFA")
    
    with col2:
        variation = dernier['Close'] - dernier['Open']
        variation_pct = ((dernier['Close'] - df.iloc[-2]['Close']) / df.iloc[-2]['Close']) * 100 if len(df) >= 2 else 0
        delta_color = "normal"
        if variation > 0:
            st.metric("Variation du jour", f"{variation:+,.0f} FCFA", delta=f"{variation_pct:+.2f}%", delta_color="normal")
        else:
            st.metric("Variation du jour", f"{variation:+,.0f} FCFA", delta=f"{variation_pct:+.2f}%", delta_color="inverse")
    
    with col3:
        st.metric("Volume", f"{dernier['Volume']:,.0f}")
    
    st.subheader("📊 Historique des cours")

# Calculer la date de début (5 ans par défaut)
    date_max = df['Date'].max()
    date_min_5ans = date_max - pd.DateOffset(years=5)

# Sélecteur de période
    periode_options = {
    "5 dernières années": date_min_5ans,
    "10 dernières années": date_max - pd.DateOffset(years=10),
    "Toute la période": df['Date'].min()
    }

    col_periode, _ = st.columns([1, 3])
    with col_periode:
      choix_periode = st.selectbox(
        "Période à afficher",
        list(periode_options.keys()),
        index=0  # 5 ans par défaut
    )

# Filtrer les données
    date_debut = periode_options[choix_periode]
    df_filtre = df[df['Date'] >= date_debut]

# Créer le graphique Plotly
    fig = px.line(
    df_filtre, 
    x='Date', 
    y='Close',
    title=f"Cours de {selected} ({choix_periode})",
    labels={'Close': 'Cours (FCFA)', 'Date': 'Date'}
    )

# Personnaliser le graphique
    fig.update_layout(
    xaxis_title="Date",
    yaxis_title="Cours (FCFA)",
    xaxis={
        "rangeselector": None,  # Supprime les boutons de zoom prédéfinis
        "type": "date"
      },
    # Empêcher le zoom/dézoom utilisateur
    dragmode=False,           # Désactive le zoom par glisser
    hovermode='x unified'     # Garde l'infobulle
    )

# Désactiver la barre d'outils de zoom
    fig.update_xaxes(fixedrange=True)   # Empêche zoom x
    fig.update_yaxes(fixedrange=True)   # Empêche zoom y

# Afficher dans Streamlit
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})  # Cache la barre d'outils
    
        # ========== MOYENNES MOBILES ==========
    st.subheader("📈 Moyennes mobiles")
    
    # Calcul des moyennes mobiles
    df['MM20'] = df['Close'].rolling(window=20).mean()
    df['MM50'] = df['Close'].rolling(window=50).mean()
    
    # Sélecteur de période pour les moyennes mobiles (réutilise la même logique)
    date_max_mm = df['Date'].max()
    date_min_5ans_mm = date_max_mm - pd.DateOffset(years=5)
    
    periode_options_mm = {
        "5 dernières années": date_min_5ans_mm,
        "10 dernières années": date_max_mm - pd.DateOffset(years=10),
        "Toute la période": df['Date'].min()
    }
    
    col_periode_mm, _ = st.columns([1, 3])
    with col_periode_mm:
        choix_periode_mm = st.selectbox(
            "Période à afficher",
            list(periode_options_mm.keys()),
            index=0,
            key="periode_mm"
        )
    
    date_debut_mm = periode_options_mm[choix_periode_mm]
    df_filtre_mm = df[df['Date'] >= date_debut_mm]
    
    # Créer le graphique avec les moyennes mobiles
    fig_mm = px.line(
        df_filtre_mm,
        x='Date',
        y=['Close', 'MM20', 'MM50'],
        title=f"Cours et moyennes mobiles de {selected} ({choix_periode_mm})",
        labels={'value': 'Cours (FCFA)', 'Date': 'Date', 'variable': 'Série'}
    )
    
    # Personnaliser les noms dans la légende
    fig_mm.update_traces(
        name='Cours',
        selector=dict(name='Close')
    )
    fig_mm.update_traces(
        name='MM20 (20 jours)',
        selector=dict(name='MM20')
    )
    fig_mm.update_traces(
        name='MM50 (50 jours)',
        selector=dict(name='MM50')
    )
    
    # Personnaliser l'apparence
    fig_mm.update_layout(
        xaxis_title="Date",
        yaxis_title="Cours (FCFA)",
        xaxis={"type": "date"},
        dragmode=False,
        hovermode='x unified',
        legend_title_text='Indicateurs'
    )
    
    # Désactiver le zoom
    fig_mm.update_xaxes(fixedrange=True)
    fig_mm.update_yaxes(fixedrange=True)
    
    # Afficher le graphique
    st.plotly_chart(fig_mm, use_container_width=True, config={'displayModeBar': False})
    
    # Interprétation simple
    dernier_cours = df['Close'].iloc[-1]
    mm20_actuelle = df['MM20'].iloc[-1]
    mm50_actuelle = df['MM50'].iloc[-1]
    
    st.markdown("**🔍 Interprétation :**")
    col_interpret1, col_interpret2, col_interpret3 = st.columns(3)
    
    with col_interpret1:
        if dernier_cours > mm20_actuelle:
            st.success(f"✅ Cours > MM20 : tendance court-terme haussière")
        else:
            st.error(f"❌ Cours < MM20 : tendance court-terme baissière")
    
    with col_interpret2:
        if dernier_cours > mm50_actuelle:
            st.success(f"✅ Cours > MM50 : tendance moyen-terme haussière")
        else:
            st.error(f"❌ Cours < MM50 : tendance moyen-terme baissière")
    
    with col_interpret3:
        if mm20_actuelle > mm50_actuelle:
            st.success(f"✅ MM20 > MM50 : signal haussier (croisement)")
        else:
            st.error(f"❌ MM20 < MM50 : signal baissier")
    
        # ========== RSI (RELATIVE STRENGTH INDEX) ==========
    st.subheader("📊 RSI - Relative Strength Index")
    
    # Fonction de calcul du RSI
    def calculer_rsi(series, periode=14):
        delta = series.diff()
        gain = delta.where(delta > 0, 0)
        perte = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=periode, min_periods=periode).mean()
        avg_loss = perte.rolling(window=periode, min_periods=periode).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    # Calcul du RSI sur 14 jours (période standard)
    df['RSI14'] = calculer_rsi(df['Close'], periode=14)
    
    # Sélecteur de période pour le RSI
    date_max_rsi = df['Date'].max()
    date_min_5ans_rsi = date_max_rsi - pd.DateOffset(years=5)
    
    periode_options_rsi = {
        "5 dernières années": date_min_5ans_rsi,
        "10 dernières années": date_max_rsi - pd.DateOffset(years=10),
        "Toute la période": df['Date'].min()
    }
    
    col_periode_rsi, _ = st.columns([1, 3])
    with col_periode_rsi:
        choix_periode_rsi = st.selectbox(
            "Période à afficher",
            list(periode_options_rsi.keys()),
            index=0,
            key="periode_rsi"
        )
    
    date_debut_rsi = periode_options_rsi[choix_periode_rsi]
    df_filtre_rsi = df[df['Date'] >= date_debut_rsi]
    
    # Créer le graphique du RSI
    fig_rsi = px.line(
        df_filtre_rsi,
        x='Date',
        y='RSI14',
        title=f"RSI 14 jours de {selected} ({choix_periode_rsi})",
        labels={'RSI14': 'RSI', 'Date': 'Date'}
    )
    
    # Ajouter les lignes seuils (30 et 70)
    fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Sur-achat (70)")
    fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Sur-vente (30)")
    fig_rsi.add_hline(y=50, line_dash="dot", line_color="gray", annotation_text="Neutre (50)")
    
    # Personnaliser le graphique
    fig_rsi.update_layout(
        xaxis_title="Date",
        yaxis_title="RSI",
        xaxis={"type": "date"},
        dragmode=False,
        hovermode='x unified',
        yaxis_range=[0, 100]
    )
    
    # Désactiver le zoom
    fig_rsi.update_xaxes(fixedrange=True)
    fig_rsi.update_yaxes(fixedrange=True)
    
    # Afficher le graphique
    st.plotly_chart(fig_rsi, use_container_width=True, config={'displayModeBar': False})
    
    # Interprétation du RSI
    dernier_rsi = df['RSI14'].iloc[-1]
    
    st.markdown("**🔍 Interprétation du RSI :**")
    col_rsi1, col_rsi2, col_rsi3 = st.columns(3)
    
    with col_rsi1:
        if dernier_rsi > 70:
            st.error(f"⚠️ RSI à {dernier_rsi:.1f} → **Zone de sur-achat** (risque de correction)")
        elif dernier_rsi < 30:
            st.success(f"✅ RSI à {dernier_rsi:.1f} → **Zone de sur-vente** (opportunité d'achat potentielle)")
        else:
            st.info(f"ℹ️ RSI à {dernier_rsi:.1f} → Zone neutre")
    
    with col_rsi2:
        if dernier_rsi > 70 and df['Close'].iloc[-1] > df['Close'].iloc[-2]:
            st.warning("📉 Divergence baissière possible (prix haut, RSI suracheté)")
        elif dernier_rsi < 30 and df['Close'].iloc[-1] < df['Close'].iloc[-2]:
            st.info("📈 Divergence haussière possible (prix bas, RSI survendu)")
    
    with col_rsi3:
        # Signal de croisement de la ligne 50
        rsi_avant_dernier = df['RSI14'].iloc[-2]
        if rsi_avant_dernier < 50 and dernier_rsi > 50:
            st.success("🟢 Signal haussier : RSI passe au-dessus de 50")
        elif rsi_avant_dernier > 50 and dernier_rsi < 50:
            st.error("🔴 Signal baissier : RSI passe en dessous de 50")
        # ========== BANDES DE BOLLINGER ==========
    st.subheader("📊 Bandes de Bollinger")
    
    # Calcul des Bandes de Bollinger (période 20, écart-type 2)
    periode_bb = 20
    std_dev = 2
    
    df['BB_M20'] = df['Close'].rolling(window=periode_bb).mean()
    df['BB_std'] = df['Close'].rolling(window=periode_bb).std()
    df['BB_sup'] = df['BB_M20'] + (std_dev * df['BB_std'])
    df['BB_inf'] = df['BB_M20'] - (std_dev * df['BB_std'])
    
    # Sélecteur de période pour les Bandes de Bollinger
    date_max_bb = df['Date'].max()
    date_min_5ans_bb = date_max_bb - pd.DateOffset(years=5)
    
    periode_options_bb = {
        "5 dernières années": date_min_5ans_bb,
        "10 dernières années": date_max_bb - pd.DateOffset(years=10),
        "Toute la période": df['Date'].min()
    }
    
    col_periode_bb, _ = st.columns([1, 3])
    with col_periode_bb:
        choix_periode_bb = st.selectbox(
            "Période à afficher",
            list(periode_options_bb.keys()),
            index=0,
            key="periode_bb"
        )
    
    date_debut_bb = periode_options_bb[choix_periode_bb]
    df_filtre_bb = df[df['Date'] >= date_debut_bb]
    
    # Créer le graphique des Bandes de Bollinger
    fig_bb = px.line(
        df_filtre_bb,
        x='Date',
        y=['Close', 'BB_M20', 'BB_sup', 'BB_inf'],
        title=f"Bandes de Bollinger de {selected} ({choix_periode_bb}) - Période {periode_bb}, {std_dev} écarts-types",
        labels={'value': 'Cours (FCFA)', 'Date': 'Date', 'variable': 'Série'}
    )
    
    # Personnaliser les noms dans la légende
    fig_bb.update_traces(name='Cours', selector=dict(name='Close'))
    fig_bb.update_traces(name=f'MM{periode_bb}', selector=dict(name='BB_M20'))
    fig_bb.update_traces(name='Bande supérieure (+2σ)', selector=dict(name='BB_sup'))
    fig_bb.update_traces(name='Bande inférieure (-2σ)', selector=dict(name='BB_inf'))
    
    # Personnaliser l'apparence
    fig_bb.update_layout(
        xaxis_title="Date",
        yaxis_title="Cours (FCFA)",
        xaxis={"type": "date"},
        dragmode=False,
        hovermode='x unified',
        legend_title_text='Bandes de Bollinger',
        # Ajouter une zone colorée entre les bandes (optionnel)
        shapes=[
            dict(
                type="rect",
                xref="paper", x0=0, x1=1,
                yref="y", y0=df_filtre_bb['BB_inf'].min(), y1=df_filtre_bb['BB_sup'].max(),
                fillcolor="rgba(0, 100, 200, 0.05)",
                layer="below",
                line_width=0,
            )
        ]
    )
    
    # Désactiver le zoom
    fig_bb.update_xaxes(fixedrange=True)
    fig_bb.update_yaxes(fixedrange=True)
    
    # Afficher le graphique
    st.plotly_chart(fig_bb, use_container_width=True, config={'displayModeBar': False})
    
    # Interprétation des Bandes de Bollinger
    dernier_cours_bb = df['Close'].iloc[-1]
    derniere_bande_sup = df['BB_sup'].iloc[-1]
    derniere_bande_inf = df['BB_inf'].iloc[-1]
    derniere_mm20 = df['BB_M20'].iloc[-1]
    largeur_bandes = derniere_bande_sup - derniere_bande_inf
    largeur_moyenne = (df['BB_sup'] - df['BB_inf']).mean()
    
    # Détection des squeezes (bandes très serrées)
    squeeze = largeur_bandes < (largeur_moyenne * 0.7)
    
    st.markdown("**🔍 Interprétation des Bandes de Bollinger :**")
    col_bb1, col_bb2, col_bb3 = st.columns(3)
    
    with col_bb1:
        if dernier_cours_bb >= derniere_bande_sup:
            st.error(f"⚠️ Cours à **{dernier_cours_bb:,.0f}** ≥ bande supérieure ({derniere_bande_sup:,.0f}) → **Sur-extension haussière**, possible consolidation")
        elif dernier_cours_bb <= derniere_bande_inf:
            st.success(f"✅ Cours à **{dernier_cours_bb:,.0f}** ≤ bande inférieure ({derniere_bande_inf:,.0f}) → **Sur-extension baissière**, possible rebond")
        else:
            st.info(f"ℹ️ Cours dans le canal ({derniere_bande_inf:,.0f} - {derniere_bande_sup:,.0f}) → Zone normale")
    
    with col_bb2:
        if squeeze:
            st.warning(f"⚠️ **Squeeze** : bandes très serrées ({largeur_bandes:,.0f} FCFA) → forte volatilité imminente")
        else:
            st.info(f"ℹ️ Largeur normale des bandes : {largeur_bandes:,.0f} FCFA")
    
    with col_bb3:
        # Signal de sortie de bande
        if dernier_cours_bb > derniere_bande_sup and df['Close'].iloc[-2] <= df['BB_sup'].iloc[-2]:
            st.success("🟢 Signal : sortie par le haut → tendance haussière forte")
        elif dernier_cours_bb < derniere_bande_inf and df['Close'].iloc[-2] >= df['BB_inf'].iloc[-2]:
            st.success("🟢 Signal : sortie par le bas → tendance baissière forte")
    
    # Affichage des valeurs actuelles
    with st.expander("📊 Détails des valeurs actuelles"):
        st.write(f"- **Cours actuel** : {dernier_cours_bb:,.0f} FCFA")
        st.write(f"- **MM20** : {derniere_mm20:,.0f} FCFA")
        st.write(f"- **Bande supérieure (+2σ)** : {derniere_bande_sup:,.0f} FCFA")
        st.write(f"- **Bande inférieure (-2σ)** : {derniere_bande_inf:,.0f} FCFA")
        st.write(f"- **Largeur des bandes** : {largeur_bandes:,.0f} FCFA")
        if squeeze:
            st.write("- **⚠️ Squeeze détecté** : forte volatilité à venir")
    
    st.subheader("📋 Dernières séances")
    st.dataframe(df.tail(10).sort_values('Date', ascending=False))
else:
 st.warning(f"⚠️ Données non disponibles pour {selected}")

# ========== 5. COMPARAISON MULTI-VALEURS ==========
st.markdown("---")
st.subheader("📊 Comparaison de valeurs")

multi_tickers = st.multiselect(
    "Sélectionnez 2 à 4 valeurs à comparer",
    tickers_brvm,
    default=["ABJC", "BOAS", "ORAC"]
)

if len(multi_tickers) >= 2:
    # Charger les données et les aligner sur les mêmes dates
    data_compare = {}
    dates_communes = None
    
    for ticker in multi_tickers:
        df_temp = charger_donnees(ticker)
        if df_temp is not None and not df_temp.empty:
            # Série des prix de clôture avec index Date
            serie = df_temp.set_index('Date')['Close']
            data_compare[ticker] = serie
            
            # Trouver l'intersection des dates (pour avoir les mêmes dates partout)
            if dates_communes is None:
                dates_communes = serie.index
            else:
                dates_communes = dates_communes.intersection(serie.index)
    
    if len(data_compare) >= 2:
        # Reindexer toutes les séries sur les dates communes
        df_compare = pd.DataFrame({
            ticker: data_compare[ticker].reindex(dates_communes)
            for ticker in data_compare
        })
        
        # Supprimer les lignes avec des NaN
        df_compare = df_compare.dropna()
        
        if not df_compare.empty:
            # Normaliser les prix (base 100 à la première date commune)
            df_normalized = df_compare / df_compare.iloc[0] * 100
            
            # Sélecteur de période
            date_max = df_normalized.index.max()
            date_min_5ans = date_max - pd.DateOffset(years=5)
            
            periode_options = {
                "5 dernières années": date_min_5ans,
                "10 dernières années": date_max - pd.DateOffset(years=10),
                "Toute la période": df_normalized.index.min()
            }
            
            col_periode, _ = st.columns([1, 3])
            with col_periode:
                choix_periode = st.selectbox(
                    "Période à afficher",
                    list(periode_options.keys()),
                    index=0,
                    key="periode_comparaison"
                )
            
            # Filtrer les données
            date_debut = periode_options[choix_periode]
            df_filtre = df_normalized[df_normalized.index >= date_debut]
            
            if not df_filtre.empty:
                # Créer le graphique Plotly
                fig = px.line(
                    df_filtre,
                    title=f"Comparaison des cours normalisés ({choix_periode})",
                    labels={'value': 'Cours normalisés (base 100)', 'Date': 'Date', 'variable': 'Ticker'}
                )
                
                fig.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Cours normalisés (base 100)",
                    xaxis={"type": "date"},
                    dragmode=False,
                    hovermode='x unified',
                    legend_title_text='Valeurs'
                )
                
                fig.update_xaxes(fixedrange=True)
                fig.update_yaxes(fixedrange=True)
                
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                st.caption("📌 Cours normalisés (base 100 = début de la période affichée). Seules les dates communes à toutes les valeurs sont affichées.")
            else:
                st.warning("Aucune donnée disponible pour la période sélectionnée")
        else:
            st.warning("Pas de dates communes entre les valeurs sélectionnées")
    else:
        st.warning(f"Impossible de charger suffisamment de données. Chargés : {list(data_compare.keys())}")
else:
    st.info("Sélectionnez au moins 2 valeurs pour comparer")
# ========== INDICATEURS MACRO (dernière date disponible) ==========

@st.cache_data(ttl=86400)
def get_last_macro_indicators():
    """Charge et retourne uniquement la dernière ligne des indicateurs macro"""
    url = "https://raw.githubusercontent.com/spoudar/brvm-data-automation/main/data/brvm_market_data.csv"
    
    try:
        # Lire le CSV
        df = pd.read_csv(url)
        
        # Nettoyer la date (garder uniquement la partie JJ/MM/AAAA)
        df['Date'] = df['Date'].astype(str).str[:10]
        
        # Nettoyer les colonnes numériques (supprimer les espaces)
        for col in ['Valeur_des_transactions', 'Capitalisation_Actions', 'Capitalisation_Obligations', 
                    'BRVM_10', 'BRVM_Composite', 'BRVM_PRESTIGE']:
            if col in df.columns:
                # Supprimer les espaces et convertir en nombre
                df[col] = df[col].astype(str).str.replace(' ', '').str.replace(',', '.')
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Convertir en milliards pour l'affichage
        df['Valeur_des_transactions_Mds'] = df['Valeur_des_transactions'] / 1e9
        df['Capitalisation_Actions_Mds'] = df['Capitalisation_Actions'] / 1e12
        df['Capitalisation_Obligations_Mds'] = df['Capitalisation_Obligations'] / 1e12
        
        # Garder uniquement la première ligne (la plus récente car le fichier est trié)
        df = df.head(1)
        
        return df
    except Exception as e:
        st.error(f"Erreur : {e}")
        return None

# Affichage
df_macro = get_last_macro_indicators()

if df_macro is not None and not df_macro.empty:
    st.markdown("---")
    st.subheader("🏛️ Synthèse du marché BRVM")
    
    # Récupérer la ligne unique
    row = df_macro.iloc[0]
    
    # Première ligne : Date
    st.info(f"📅 **Séance du {row['Date']} à 09h30**")
    
    # Deuxième ligne : Valeur des transactions, Capitalisations
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "💰 Valeur des transactions",
            f"{row['Valeur_des_transactions_Mds']:,.2f} Mds FCFA"
        )
    
    with col2:
        st.metric(
            "📊 Capitalisation Actions",
            f"{row['Capitalisation_Actions_Mds']:,.2f} Mds FCFA"
        )
    
    with col3:
        st.metric(
            "📈 Capitalisation Obligations",
            f"{row['Capitalisation_Obligations_Mds']:,.2f} Mds FCFA"
        )
    
    # Troisième ligne : Indices
    col4, col5, col6 = st.columns(3)
    
    with col4:
        st.metric("📉 BRVM Composite", f"{row['BRVM_Composite']:.2f}")
    
    with col5:
        st.metric("📊 BRVM 10", f"{row['BRVM_10']:.2f}")
    
    with col6:
        st.metric("⭐ BRVM Prestige", f"{row['BRVM_PRESTIGE']:.2f}")
    
    # Quatrième ligne : Taux BRVM 10
    st.caption(f"📈 Variation BRVM 10 : {row['Taux_BRVM_10']}")
    
else:
    st.info("📊 Indicateurs macroéconomiques temporairement indisponibles")
st.markdown("---")
col_footer1, col_footer2 = st.columns(2)
with col_footer1:
    st.caption(f"📅 Dernière mise à jour : {datetime.now().strftime('%d/%m/%Y à %H:%M')}")

st.markdown("---")
# ========== RÉSEAUX SOCIAUX ==========
st.markdown("---")
st.markdown("### 🔗 Suivez-moi")

# Créer 3 colonnes pour les boutons
col_social1, col_social2, col_social3, col_social4 = st.columns(4)

# Liens à personnaliser avec vos URLs
youtube_url = "https://youtube.com/@SiéPOUDAR"
facebook_url = "https://facebook.com/EasyscienceFbk?locale=fr_FR"
linkedin_url = "https://linkedin.com/in/sié-poudar-67173a25b"
twitter_url = "https://twitter.com/votre_compte"  # Optionnel

with col_social1:
    st.markdown(f"""
        <a href="{youtube_url}" target="_blank">
            <div style="
                background-color: #FF0000;
                padding: 10px;
                border-radius: 10px;
                text-align: center;
                color: white;
                text-decoration: none;
                font-weight: bold;
            ">
                ▶️ YouTube
            </div>
        </a>
    """, unsafe_allow_html=True)

with col_social2:
    st.markdown(f"""
        <a href="{facebook_url}" target="_blank">
            <div style="
                background-color: #1877F2;
                padding: 10px;
                border-radius: 10px;
                text-align: center;
                color: white;
                text-decoration: none;
                font-weight: bold;
            ">
                📘 Facebook
            </div>
        </a>
    """, unsafe_allow_html=True)

with col_social3:
    st.markdown(f"""
        <a href="{linkedin_url}" target="_blank">
            <div style="
                background-color: #0077B5;
                padding: 10px;
                border-radius: 10px;
                text-align: center;
                color: white;
                text-decoration: none;
                font-weight: bold;
            ">
                🔗 LinkedIn
            </div>
        </a>
    """, unsafe_allow_html=True)

with col_social4:
    st.markdown(f"""
        <a href="{twitter_url}" target="_blank">
            <div style="
                background-color: #1DA1F2;
                padding: 10px;
                border-radius: 10px;
                text-align: center;
                color: white;
                text-decoration: none;
                font-weight: bold;
            ">
                🐦 Twitter
            </div>
        </a>
    """, unsafe_allow_html=True)

st.caption("📊 Données : BRVM | Développé avec Streamlit")