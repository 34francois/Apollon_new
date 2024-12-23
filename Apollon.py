import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components
import numpy as np
import re
import plotly.express as px
import base64  
import pdfkit
from tempfile import NamedTemporaryFile
import matplotlib.pyplot as plt

# Configuration de la page
st.set_page_config(
    page_title="APOLLON 2.0",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.sidebar.image("/home/francois/Documents/ACROPOLE/Dashboard/dash_1/Apollon_logo.png", width=380)
st.image("/home/francois/Documents/ACROPOLE/Dashboard/dash_1/Daumier_bandeau.png", use_column_width=False, width=400)

# Initialisation dans st.session_state
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame({
        "ELEVE": pd.Series(dtype='str'),
        "NOM": pd.Series(dtype='str'),
        "PRENOM": pd.Series(dtype='str'),
        "GENRE": pd.Series(dtype='str'),
        "Classe": pd.Series(dtype='str'),
        "Niveau": pd.Series(dtype='str'),
        "OPTION1": pd.Series(dtype='str'),
        "OPTION2": pd.Series(dtype='str'),
        "OPTION3": pd.Series(dtype='str'),
        "OPTION4": pd.Series(dtype='str'),
        "OPTION5": pd.Series(dtype='str'),
        "MOYENNE": pd.Series(dtype='int'),
        "COMPORTEMENT": pd.Series(dtype='int'),
        "PUNITION": pd.Series(dtype='int'),
        "SANCTION": pd.Series(dtype='int'),
        "EXCLUSION_COURS": pd.Series(dtype='int'),
        "ABSENCE": pd.Series(dtype='int'),
        "RETARD": pd.Series(dtype='int'),
        "PROFIL": pd.Series(dtype='str'),
        "DEGRE_DECROCHAGE": pd.Series(dtype='str'),
        "Classe_precedente": pd.Series(dtype='str'),
        "HISTOIRE": pd.Series(dtype='int'),
        "FRANCAIS": pd.Series(dtype='int'),
        "MATHEMATIQUES": pd.Series(dtype='int'),
        "SVT": pd.Series(dtype='int'),
        "PHYSIQUE": pd.Series(dtype='int'),
        "LV1": pd.Series(dtype='int'),
        "LV2": pd.Series(dtype='int'),
        "LV3": pd.Series(dtype='int'),
        "ARTS": pd.Series(dtype='int'),
        "MUSIQUE": pd.Series(dtype='int'),
        "EPS": pd.Series(dtype='int'),
        "TECHNOLOGIE": pd.Series(dtype='int'),
    })


# Chargement et formatage du CSV
with st.sidebar.expander("Charger les données des élèves"):
    uploaded_file = st.file_uploader("Choisir un fichier CSV", type=["csv"])
    if uploaded_file is not None:
        if uploaded_file.getvalue():
            separator = st.text_input("Entrez le séparateur de données (par défaut : tabulation) :", value="\t")
            try:
                new_df = pd.read_csv(uploaded_file, encoding='UTF-8', sep=separator, header=0)
                st.write("Aperçu des données :")
                # Formater l'affichage des nombres en exponentiel
                new_df = new_df.applymap(lambda x: '{:.2e}'.format(x) if isinstance(x, (int, float)) else x)

                column_mapping = {}
                for col in new_df.columns:
                    options = ["Ignorer"] + list(st.session_state.df.columns)
                    default_index = 0
                    if col in st.session_state.df.columns:
                        default_index = options.index(col)
                    column_mapping[col] = st.selectbox(f"Colonne pour '{col}' :", options=options, index=default_index, key=col)

                mapped_df = new_df[[col for col, mapped_col in column_mapping.items() if mapped_col != "Ignorer"]]
                mapped_df = mapped_df.rename(columns={col: mapped_col for col, mapped_col in column_mapping.items() if mapped_col != "Ignorer"})

                if st.button("Concaténer"):
                    try:
                        st.session_state.df = pd.concat([st.session_state.df, mapped_df], ignore_index=True)
                        st.success("Données concaténées avec succès!")
                        # Remplacer ".00e+00" par "ème"
                        st.session_state.df = st.session_state.df.replace(r"\.00e\+0", "ème", regex=True)
                        # Compléter la colonne "ELEVE"
                        st.session_state.df["ELEVE"] = st.session_state.df.apply(lambda row: row["NOM"] + " " + row["PRENOM"], axis=1)

                        st.write("DataFrame mis à jour :")
                    except Exception as e:
                        st.error(f"Erreur lors de la concaténation : {e}")
            except (UnicodeDecodeError, pd.errors.EmptyDataError) as e:
                st.error(f"Erreur lors du chargement du fichier : {e}")
                st.stop()
        else:
            st.warning("Le fichier CSV est vide. Veuillez télécharger un fichier contenant des données.")

# Chargement et fusion des données supplémentaires
with st.sidebar.expander("Charger des données supplémentaires"):
    uploaded_file_supp = st.file_uploader("Choisir un fichier CSV pour les données supplémentaires", type=["csv"])
    if uploaded_file_supp is not None:
        try:
            df_supp = pd.read_csv(uploaded_file_supp, encoding='UTF-8', sep="\t")  # Assurez-vous d'utiliser le bon séparateur
            st.write("Aperçu des données supplémentaires :")
            st.dataframe(df_supp.head())

            column_mapping_supp = {}
            for col in df_supp.columns:
                if col != "ELEVE":  # On ne mappe pas la colonne "ELEVE"
                    options = ["Ignorer"] + list(st.session_state.df.columns)
                    column_mapping_supp[col] = st.selectbox(f"Colonne pour '{col}' :", options=options, key=f"supp_{col}")

            mapped_df_supp = df_supp[[col for col, mapped_col in column_mapping_supp.items() if mapped_col != "Ignorer"]]
            mapped_df_supp = mapped_df_supp.rename(columns={col: mapped_col for col, mapped_col in column_mapping_supp.items() if mapped_col != "Ignorer"})

            if st.button("Fusionner"):
                try:
                    # Fusionner les DataFrames sur "ELEVE" avec suffixes
                    merged_df = pd.merge(st.session_state.df, mapped_df_supp, on="ELEVE", how="left", suffixes=("_x", "_y"))  

                    # Mettre à jour les valeurs du DataFrame principal
                    for col in mapped_df_supp.columns:
                        if col != "ELEVE": 
                            st.session_state.df.update(merged_df[[col + "_y"]].rename(columns={col + "_y": col}))

                    # Supprimer les colonnes "_x"
                    st.session_state.df = st.session_state.df[[col for col in st.session_state.df.columns if not col.endswith("_x")]]
                    for col in ["MOYENNE", "COMPORTEMENT", "ABSENCE"]:
                        st.session_state.df[col] = st.session_state.df[col].str.replace(',', '.', regex=False)

                    for col in ["MOYENNE", "COMPORTEMENT", "ABSENCE"]:
                        st.session_state.df[col] = pd.to_numeric(st.session_state.df[col], errors='coerce')

                    st.success("Données supplémentaires fusionnées avec succès!")
                    st.write("DataFrame mis à jour :")
                    st.write(st.session_state.df)

                except Exception as e:
                    st.error(f"Erreur lors de la fusion : {e}")
        except Exception as e:
            st.error(f"Erreur lors du chargement du fichier : {e}")



with st.expander("Changer la classe d'un élève"):
    liste_eleves = st.session_state.df["ELEVE"].unique().tolist()
    nom_eleve = st.selectbox("Nom de l'élève :", liste_eleves, key="selectbox_eleve")
    classes_disponibles = st.session_state.df["Classe"].unique().tolist()  # Récupérer les classes uniques
    nouvelle_classe = st.selectbox("Nouvelle classe :", classes_disponibles)

    if st.button("Changer de classe"):
        try:
            st.session_state.df.loc[st.session_state.df["ELEVE"] == nom_eleve, "Classe"] = nouvelle_classe
            st.success(f"La classe de {nom_eleve} a été changée en {nouvelle_classe}.")
            st.write("DataFrame mis à jour :")
        except Exception as e:
            st.error(f"Erreur lors du changement de classe : {e}")

with st.sidebar.expander("Changer le genre d'un élève"):
    nom_eleve_genre = st.text_input("Nom de l'élève genre :")
    genre_disponibles = st.session_state.df["GENRE"].unique().tolist()  # Récupérer les classes uniques
    nouveau_genre = st.selectbox("Nouveau genre :", genre_disponibles)

    if st.button("Changer de genre"):
        try:
            st.session_state.df.loc[st.session_state.df["NOM"] == nom_eleve_genre, "GENRE"] = nouveau_genre
            st.success(f"Le genre de {nom_eleve_genre} a été changée en {nouveau_genre}.")
            st.write("DataFrame mis à jour :")
        except Exception as e:
            st.error(f"Erreur lors du changement de genre : {e}")


with st.sidebar.expander("Tableau de donnée modifiable"):
    edited_df = st.data_editor(st.session_state.df, key="data_editor")
    if st.button("appliquer les changements"):
        st.session_state.df = edited_df
        st.rerun() #Force rerun


st.dataframe(st.session_state.df)
