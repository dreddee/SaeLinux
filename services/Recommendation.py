import pandas as pd
from sklearn.svm import SVC
from utilis.bddUtilis import RetrievePickleObject, recommendationToSQL, Retrieve_Notes_per_Serie, retrieve_subtitles_from_bdd
from sklearn.metrics import classification_report, accuracy_score
import numpy as np

def createDatasets(Evaluations,Subtitles):
    TrainDataset = Evaluations[['SerieID','Vectorised','Fullname','Note']]
    TestDataset = (Subtitles[~Subtitles['SerieID'].isin(Evaluations['SerieID'])])[['SerieID','Fullname','Vectorised']]

    return (TrainDataset,TestDataset)

def evaluate_model(model, X_train, y_train, X_test, y_test):
    # Fit the model
    model.fit(X_train, y_train)
    
    # Make predictions
    y_pred = model.predict(X_test)
    
    # Calculate metrics
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred)
    
    # Print metrics
    print("Accuracy:", accuracy)
    print("Classification Report:\n", report)

    return model

def ProcessRecommendationFull(conn,userID):
    Evaluations = Retrieve_Notes_per_Serie(conn,userID)
    subtitles = retrieve_subtitles_from_bdd(conn)
    Traindf, Testdf = createDatasets(Evaluations,subtitles)
    
    Xtrain = np.array(Traindf['Vectorised'].tolist())
    Ytrain = Traindf['Note'].values
    Xeval = np.array(Testdf['Vectorised'].tolist())

    model_best = SVC(
        C=1000,
        kernel="rbf",  # You can also try 'rbf'
        degree=2,         # Only if using polynomial kernel
        gamma='scale',    # Useful for RBF
        class_weight='balanced',  # Use if your classes are imbalanced
        max_iter=1000     # Adjust based on your needs
    )
    yeval = None
    if(len(Xtrain) > 0):
        model_best = evaluate_model(model_best,Xtrain,Ytrain,Xtrain,Ytrain)

        yeval = model_best.predict(Xeval)  # Predictions from the model
    else:
        yeval = np.full(Xeval.shape[0], 3.00)
    
    # Convert predictions to a DataFrame
    predictions_df = pd.DataFrame(yeval, columns=['Predicted_Note'])

    # Rejoin predictions with the original Testdf
    Testdf_rejoined = Testdf.reset_index(drop=True).join(predictions_df)[['SerieID','Fullname','Predicted_Note']]

    OrderRecommendation = Testdf_rejoined.sort_values('Predicted_Note',ascending=False).drop_duplicates(subset='SerieID')

    print(recommendationToSQL(conn,OrderRecommendation,userID))

def getRecommendation(userID, connection):
    try:
        # SQL query to retrieve the Recommendation for the given user
        query = """
        SELECT Recommendation
        FROM utilisateur
        WHERE ID_Utilisateur = %s;
        """
        
        # Execute the SQL query
        with connection.cursor(buffered=True) as cursor:
            cursor.execute(query, (userID,))
            result = cursor.fetchone()
            
            # If a recommendation exists, unpickle it and return
            if result and result[0]:
                recommendation = RetrievePickleObject(result[0])  # Unpickle the BLOB data
                return recommendation
            else:
                return "No recommendation found for this user."
    
    except Exception as e:
        return f"Error: {e}"