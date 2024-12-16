from utilis.bddUtilis import retrieve_subtitles_from_bdd
from utilis.utilis import unique
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd

def CreateVectoriserModel(conn):
    # Retrieve subtitles from the database (assuming you have this function implemented)
    documentsDF = retrieve_subtitles_from_bdd(conn)
    
    # Initialize the TF-IDF vectorizer
    vectorizer = TfidfVectorizer()

    # Fit the TF-IDF model and transform the documents into a TF-IDF matrix
    tfidf_matrix = vectorizer.fit_transform(documentsDF["content"])

    # Convert the TF-IDF matrix into a pandas DataFrame
    df_tfidf = pd.DataFrame(tfidf_matrix.toarray(), index=documentsDF["idSub"], columns=vectorizer.get_feature_names_out())

    # Create a dictionary with idSub as key and a tuple of (SerieID, Fullname) as value
    id_to_series_info = {row["idSub"]: (row["Fullname"], row["SerieID"]) for _, row in documentsDF.iterrows()}

    return df_tfidf, id_to_series_info

def tfidf_search_for_terms(df, terms):
    # Check if terms exist in the DataFrame
    existing_terms = [term for term in terms if term in df.columns]

    if not existing_terms:
        return "None of the terms are present in the documents."
    
    # Sum the TF-IDF values across the selected terms
    sum_tfidf = df[existing_terms].sum(axis=1)
    
    # Return the sum of TF-IDF values for each document
    return sum_tfidf[sum_tfidf != 0].sort_values(ascending=False)

def FullSearch(vectorisedModel, NameMap, recherche, n):
    Leaderboard = tfidf_search_for_terms(vectorisedModel, recherche)
    if isinstance(Leaderboard, str):
        return []
    fullnameLeaderboard = unique([ NameMap[i] for i in Leaderboard.index.tolist() ])
    return fullnameLeaderboard[:n]