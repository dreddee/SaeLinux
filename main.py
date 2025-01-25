# When connection re get everything (Recommendation, Serie Selection)
# Page switch when selecting serie and Connection and creating user
# Move user handleling to a different page
import gradio as gr
from utilis.bddUtilis import getConnection, getSerie, upsert_evaluation
from services.Search import CreateVectoriserModel, FullSearch
from services.Recommendation import ProcessRecommendationFull, getRecommendation
import os
import pandas as pd
import time
import uuid
import os

basepath = os.path.dirname(os.path.abspath(__file__))
BASE_IMAGE_PATH = os.path.join(basepath,"images")  # Répertoire où les images sont stockées dans le projet
g_Connection = getConnection(port="3306")
g_SearchVector, g_NameMap = CreateVectoriserModel(g_Connection)

COLUMNS_NUMBER = 4

def get_image_path(id_serie):
    """Retourne le chemin local de l'image pour une série donnée."""
    # Formate le nom de la série en minuscule et remplace les espaces par des underscores pour le nom du fichier
    image_file = f"{id_serie}.jpg"
    image_path = os.path.join(BASE_IMAGE_PATH, image_file)

    # Vérifie si l'image existe, sinon retourne un chemin par défaut
    if os.path.exists(image_path):
        return image_path # Retourne le chemin sous forme d'URL relative
    else:
        return f"{BASE_IMAGE_PATH}/default.jpg"  # Image par défaut si l'image spécifique n'existe pas

def rechercher_series(termes):
    resultats = FullSearch(g_SearchVector, g_NameMap, termes.lower().split(' '), 12)
    # Retourne la liste avec le chemin local de l'image correspondante ou une image par défaut
    return { res[1]:
        {
            "id": res[1], 
            "nom": res[0], 
            "image": get_image_path(res[1])  # Appelle la fonction pour obtenir le chemin de l'image locale
        }
        for res in resultats
    }

def evaluer_serie(id_utilisateur, id_serie, note, commentaire):
    upsert_evaluation(g_Connection,id_utilisateur,note,commentaire,id_serie)
    newSerieInfo = getSerie(g_Connection,id_utilisateur,id_serie)
    ProcessRecommendationFull(g_Connection,id_utilisateur)
    recommendation = obtenir_recommandations(id_utilisateur)
    return newSerieInfo, recommendation

def obtenir_recommandations(utilisateur_id):
    res = getRecommendation(utilisateur_id,g_Connection)
    return res

# Fonction de création d'utilisateur dans la base de données
def creer_utilisateur(user_name,fullname):
    user_name = user_name.lower()
    conn = g_Connection
    try:
        with conn.cursor() as cursor:
            # Générer un identifiant unique basé sur un UUID
            user_id = str(uuid.uuid4())  # Génère un identifiant unique

            # Vérifier si l'utilisateur existe déjà
            cursor.execute("SELECT ID_Utilisateur FROM utilisateur WHERE Username = %s", (user_name,))
            result = cursor.fetchone()
            if result:
                return f"Un utilisateur avec l'identifiant '{user_name}' existe déjà, veuillez réessayer."

            # Générer un code de recommandation aléatoire
            recommendation_code = None

            # Créer un nouvel utilisateur avec un identifiant unique et un code de recommandation aléatoire
            cursor.execute(
                "INSERT INTO utilisateur (ID_Utilisateur,Username , Nom, Recommendation) VALUES (%s, %s, %s, %s)",
                (user_id, user_name, fullname, recommendation_code)
            )
            conn.commit()

            ProcessRecommendationFull(g_Connection,user_id)
            return True, f"Utilisateur '{user_name}' créé avec succès avec l'identifiant '{user_id}'."
    except Exception as e:
        conn.rollback()
        return False, f"Erreur lors de la création de l'utilisateur : {e}"

def connexion_utilisateur(user_name, connectionState):
    user_name = user_name.lower()
    print(user_name)
    conn = g_Connection
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT ID_Utilisateur, Nom FROM utilisateur WHERE Username = %s", (user_name,))
            result = cursor.fetchone()
            if result:
                print("success")
                return result[0], result[1], None, True
            else:
                print("failure")
                return None, None, f"Utilisateur '{user_name}' non trouvé. Veuillez créer un compte d'abord.", connectionState
    except Exception as e:
        print(f"failure : {e}")
        return None, None, f"Erreur lors de la connexion : {e}"

# CSS Styling
css = """
    .gr-button, .gr-textbox {
        border-radius: 5px;
        margin: 10px 0;
    }
    .gr-markdown h1, .gr-markdown h2 {
        text-align: center;
        font-weight: bold;
    }
    .search-box {
        width: 40%;
        margin: 0 auto;
    }
    .result-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 20px;
        justify-content: center;
        padding: 20px 0;
    }
    .panel {
        width: 150px !important;
        text-align: center !important;
        transition: transform 0.3s !important;
    }
    .panel:hover {
        transform: scale(1.05) !important;
    }
    .panel img {
        width: 100% !important;
        height: 70% !important;
        object-fit: cover !important;
    }
    .panel h3 {
        font-size: 16px !important;
        margin: 10px 0 !important;
    }
"""

# Interface de recherche
with gr.Blocks(css=css) as app:
    gr.Markdown("# Recherche et évaluation des séries")

    informations_serie_selectionnee = gr.State(None)
    resultat_recherche_series = gr.State({})
    derniere_recherche_series = gr.State("")

    userIDState = gr.State(None)
    connectedState = gr.State(False)
    userFullname = gr.State(None)
    message_connexion =  gr.State(None)

    creation_state = gr.State(None)
    message_creation =  gr.State(None)

    recommended = gr.State(None)
    temps_recherche = gr.State(0)

    def selectionner_serie(serieID,userID):
        res = getSerie(g_Connection,userID,serieID)

        return res

    # Page de création d'utilisateur
    with gr.Tab("Créer un utilisateur"):
        user_id_creation = gr.Textbox(label="login de l'utilisateur", placeholder="Entrez un nouvel login")
        user_fullname = gr.Textbox(label="Nom complet de l'utilisateur", placeholder="Entrez votre nom complet")
        bouton_creation = gr.Button("Créer l'utilisateur")
        @gr.render(inputs=[creation_state, message_creation])
        def connexion_message(creation_state, message):
            if message:
                if creation_state:
                    gr.Info(message)
                else:
                    raise gr.Error(message)

        bouton_creation.click(fn=creer_utilisateur, inputs=[user_id_creation,user_fullname], outputs=[creation_state,message_creation]).then(None, None, None, js="() => document.getElementById('ConnexionTab-button').click()")
    with gr.Tab("Connexion", elem_id="ConnexionTab") as ConnexionTab:
        user_id_connexion = gr.Textbox(label="Nom d'utilisateur", placeholder="Entrez votre login")
        bouton_connexion = gr.Button("Se connecter")
        
        @gr.render(inputs=[userIDState, message_connexion])
        def connexion_message(id_user, message):
            if message:
                if id_user:
                    gr.Info(message)
                else:
                    raise gr.Error(message)
    # Page de recherche
    with gr.Tab("Rechercher des séries",elem_id="RechercheTab",render=False) as RechercheTab:
        recherche_serie = gr.Textbox(label="Rechercher une série", placeholder="Entrez le nom de la série...", elem_id="search-box")
        search_button = gr.Button("Rechercher")

        @gr.render(inputs=[resultat_recherche_series, derniere_recherche_series,temps_recherche],triggers=[temps_recherche.change])
        def afficher_recherche(p_resultats,recherche,temps_recherche):
            resultats = p_resultats.copy()
            start_time = time.time()
            if not recherche or len(recherche) == 0:
                gr.Markdown("## No Input Provided")
            else:
                # Create a copy of the resultats list
                with gr.Column():
                    # Convert dictionary items to a list of tuples (key, value) and iterate in steps of 3
                    resultats_items = list(resultats.items())  # Convert dict to list of tuples
                    for i in range(0, len(resultats_items), COLUMNS_NUMBER):  # Loop in steps of 3
                        with gr.Row(equal_height=True):
                            for j in range(COLUMNS_NUMBER):
                                if i + j < len(resultats_items):  # Prevent going out of bounds
                                    # Get key-value pair from the dictionary
                                    _, value = resultats_items[i + j]
                                    with gr.Column(variant='panel'):
                                        gr.Image(value["image"],format("jpg"),scale=10,show_download_button=False,show_fullscreen_button=False,show_label=False)
                                        gr.Markdown(f"""### {value["nom"]}""") 
                                        textBox = gr.Button(f"Sélectionner",scale=1)
                                        textBox.click(fn=lambda user_id, select=value["id"]: selectionner_serie(select,user_id), inputs=[userIDState], outputs=[informations_serie_selectionnee]).then(None, None, None, js="() => document.getElementById('EvaluateTab-button').click()")
                                else:
                                    with gr.Column(variant='panel'):
                                        pass
                elapsed_time = round(time.time() - start_time,3)
                gr.Markdown(f"# {len(resultats)} results for {recherche} in {temps_recherche}s ({elapsed_time}s d'affichage)") 
        # def afficher_recherche(resultats, recherche):
        #     contenu_html = '<div class="result-grid">'
        #     for serie in resultats:
        #         contenu_html += f"""
        #             <div class="card">
        #                 <img src="{serie['image']}" alt="Image de {serie['nom']}" />
        #                 <h3>{serie['nom']}</h3>
        #                 <button class="gr-button" onclick="selectionnerSerie({serie['id']})">Sélectionner</button>
        #             </div>
        #         """

        @search_button.click(inputs=recherche_serie, outputs=[resultat_recherche_series, derniere_recherche_series, temps_recherche],trigger_mode='always_last')
        def rechercher_et_afficher(termes):
            # Start the timer
            start_time = time.time()
            
            # Perform the search
            resultats_recherche = rechercher_series(termes)
            
            # Calculate the time taken
            elapsed_time = time.time() - start_time
            
            # Return the results, search terms, and elapsed time
            return resultats_recherche, termes, round(elapsed_time,3)

    # Page d'évaluation
    with gr.Tab("Évaluer une série",elem_id="EvaluateTab",render=False) as EvaluateTab:
        @gr.render(inputs=[informations_serie_selectionnee,recommended])
        def page_evaluation(p_informations_serie_selectionnee,recommendedContent):
            if p_informations_serie_selectionnee:
                name = p_informations_serie_selectionnee["Fullname"]
                id = p_informations_serie_selectionnee["SerieID"]
                gr.Markdown(f"## {name}")
                
                df = recommendedContent

                filtered_df = df.loc[df['SerieID'] == id]
                if not filtered_df.empty:
                    result = filtered_df.iloc[0]
                    predicted_note = result["Predicted_Note"]
                    # Convert Predicted_Note to a 1-5 star scale
                    stars = "★" * int(predicted_note) + "☆" * (5 - int(predicted_note))
                    display_start = f"Recommended {stars}"
                    gr.Markdown(display_start)
                else:
                    Note = p_informations_serie_selectionnee["Note"]
                    stars = "★" * int(Note) + "☆" * (5 - int(Note))
                    display_start = f"Evaluated at {stars}"
                    gr.Markdown(display_start)
                
                # Star rating input
                star_rating = gr.Radio(
                    choices=["★☆☆☆☆", "★★☆☆☆", "★★★☆☆", "★★★★☆", "★★★★★"],
                    label="Your Rating",
                    type="index"  # This returns 0-4; we can map this to 1-5
                )
                
                # User input for comments
                user_comment = gr.Textbox(label="Your Comment", placeholder="Write your thoughts about the series...")
                
                
                # Button to submit rating and comment
                submit_button = gr.Button("Submit Evaluation")
                submit_button.click(fn=lambda user_id, note, comment, select=id: evaluer_serie(user_id,select,note+1,comment) , inputs=[userIDState,star_rating,user_comment], outputs=[informations_serie_selectionnee,recommended])
            else:
                gr.Markdown("## Aucune série sélectionnée")
    
        # Page d'évaluation
    with gr.Tab("Pour vous" ,render=False) as RecommendationTab:
        @gr.render(inputs=[recommended])
        def page_recommendation(recommendation):
            COLUMNS_NUMBER = 4
            
            # Check if the input is a DataFrame
            if isinstance(recommendation, pd.DataFrame):
                display_text = "## Recommended Series:\n"
                gr.Markdown(display_text)

                with gr.Column():
                    # Loop through each row in order
                    resultats_items = recommendation.to_dict('records')
                    for i in range(0, len(resultats_items), COLUMNS_NUMBER):
                        with gr.Row(equal_height=True):
                            for j in range(COLUMNS_NUMBER):
                                if i + j < len(resultats_items):
                                    row = resultats_items[i + j]
                                    # Get the fullname and predicted note
                                    id = row['SerieID']
                                    fullname = row['Fullname']
                                    predicted_note = row['Predicted_Note']
                                    imagepath = get_image_path(id)
                                    
                                    # Convert Predicted_Note to a 1-5 star scale
                                    stars = "★" * int(predicted_note) + "☆" * (5 - int(predicted_note))
                                    
                                    # Append to display text
                                    display_text = f"### {fullname}"
                                    display_start = f"Evaluation {stars}"

                                    with gr.Column(variant="panel") as col:
                                        gr.Image(imagepath,format("jpg"),scale=10,show_download_button=False,show_fullscreen_button=False,show_label=False)
                                        gr.Markdown(display_text)
                                        gr.Markdown(display_start) 
                                        textBox = gr.Button(f"Sélectionner",scale=1)
                                        textBox.click(fn=lambda user_id, select=id: selectionner_serie(select,user_id), inputs=[userIDState], outputs=[informations_serie_selectionnee]).then(None, None, None, js="() => document.getElementById('EvaluateTab-button').click()")
                                else:
                                    with gr.Column(variant="panel"):
                                        pass
            else:
                # Display message if input is not a DataFrame
                gr.Markdown("## Aucune série recommandée")
    

    @gr.render(inputs=[userIDState],triggers=[connectedState.change])
    def render_tabs(UserID):
        if UserID != None:
            RechercheTab.render()
            EvaluateTab.render()  # Dynamically render the tab
            RecommendationTab.render()
    with ConnexionTab:
        bouton_connexion.click(fn=connexion_utilisateur, inputs=[user_id_connexion,connectedState], outputs=[userIDState,userFullname,message_connexion,connectedState]).then(fn=obtenir_recommandations, inputs=[userIDState], outputs=[recommended])#.then(None, None, None, js="() => document.getElementById('RechercheTab-button').click()")
# Lancer l'application
app.launch()
