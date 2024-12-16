import mysql.connector
import pickle
import base64
import pandas as pd
from mysql.connector import Error

def getConnection(host="localhost",user="root",password=None,port="3306",database="saeserie",charset='utf8mb4'):
    conn = mysql.connector.connect(
        host=host,  # Remplacez par votre hôte MySQL
        user=user,  # Remplacez par votre nom d'utilisateur
        password=password if password else "",  # Remplacez par votre mot de passe
        port=port,
        database=database,  # Remplacez par le nom de votre base de données
        charset=charset
    )
    return conn

def retrieve_subtitles_from_bdd(conn):
    query = """
     SELECT ID_SousTitre AS idSub, serie.ID_Serie as SerieID, serie.Titre_ as Fullname, Texte as content, sous_titre.Vectorised as Vectorised
    FROM sous_titre INNER JOIN serie
    ON serie.ID_Serie = sous_titre.ID_Série;
    """
    # Exécution de la requête et récupération des données
    df = pd.read_sql_query(query, conn )
    df['Vectorised'] = df['Vectorised'].apply(RetrievePickleObject)
    
    return df

def SetPickleObject(obj):
    pickled_object = pickle.dumps(obj)
    encoded_pickle = base64.b64encode(pickled_object).decode('utf-8')
    return encoded_pickle

def RetrievePickleObject(obj):
    return pickle.loads(base64.b64decode(obj.encode('utf-8')))

def getSerie(conn,userID,serieID):
    query= """
            SELECT 
                serie.ID_Serie AS SerieID, 
                serie.Titre_ AS Fullname, 
                evaluation.Note AS Note
            FROM 
                serie
            LEFT JOIN 
                evaluation 
            ON 
                evaluation.ID_Serie = serie.ID_Serie 
                AND evaluation.ID_Utilisateur = %s
            WHERE 
                serie.ID_Serie = %s;

         """

    # Execute the query using the cursor
    cursor = conn.cursor(dictionary=True)  # Use dictionary=True to return rows as dictionaries
    cursor.execute(query, (userID, serieID))
    
    # Fetch the first row
    result = cursor.fetchone()
    
    # Close the cursor
    cursor.close()
    
    return result  # Returns None if no result is found

def upsert_evaluation(connection, id_evaluation, note, commentaire, id_serie):
    try:
        cursor = connection.cursor()
        # Upsert query
        query = """CALL upsert_evaluation(%s,%s,%s,%s)
        """
        # Execute the query with the provided values
        cursor.execute(query, (id_evaluation, note, commentaire, id_serie))
        
        # Commit the transaction
        connection.commit()
        
        print("Upsert successful.")
    except Error as e:
        print(f"Error: {e}")
        connection.rollback()  # Rollback in case of error
    finally:
        cursor.close()

def Retrieve_Notes_per_Serie(conn,id_utilisateur):

    # Requête SQL corrigée pour utiliser la colonne 'Titre_'
    query = """
    SELECT T1.SerieID as SerieID, T1.Fullname as Fullname, sous_titre.Vectorised as Vectorised, sous_titre.Langue as 'Language' ,T1.Note as Note
    FROM sous_titre INNER JOIN
    (SELECT evaluation.ID_Serie as SerieID, serie.Titre_ as Fullname, evaluation.Note as Note
    FROM evaluation
    JOIN serie ON evaluation.ID_Serie = serie.ID_Serie
    WHERE evaluation.ID_Utilisateur = %s) as T1
    ON sous_titre.ID_Série = T1.SerieID;
    """

    # Exécution de la requête et récupération des données
    df = pd.read_sql_query(query, conn, params=(id_utilisateur,))
    df['Vectorised'] = df['Vectorised'].apply(RetrievePickleObject)
    
    return df

def recommendationToSQL(conn, Recommendation, userID):
    try:
        # Serialize the Recommendation object using pickle
        pickled_recommendation = SetPickleObject(Recommendation)
        
        # SQL query to update the user's recommendation
        query = """
        UPDATE utilisateur
        SET Recommendation = %s
        WHERE ID_Utilisateur = %s;
        """
        
        # Execute the SQL query
        with conn.cursor() as cursor:
            cursor.execute(query, (pickled_recommendation, userID))
            conn.commit()
        
        return "Recommendation updated successfully."
    
    except Exception as e:
        conn.rollback()  # Rollback in case of error
        return f"Error: {e}"
