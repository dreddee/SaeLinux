import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
from sklearn.svm import SVC

# Import des fonctions du fichier 
from services.Recommendation import createDatasets, evaluate_model, ProcessRecommendationFull, getRecommendation

class TestRecommendationModule(unittest.TestCase):

    def setUp(self):
        # Création de données simulées pour les tests
        self.evaluations = pd.DataFrame({
            'SerieID': [1, 2, 3],
            'Vectorised': [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]],
            'Fullname': ['Serie A', 'Serie B', 'Serie C'],
            'Note': [5, 3, 4]
        })

        self.subtitles = pd.DataFrame({
            'SerieID': [2, 3, 4],
            'Vectorised': [[0.3, 0.4], [0.5, 0.6], [0.7, 0.8]],
            'Fullname': ['Serie B', 'Serie C', 'Serie D']
        })

    def test_createDatasets(self):
        train, test = createDatasets(self.evaluations, self.subtitles)

        # Assertions pour vérifier les datasets
        self.assertEqual(len(train), 3)
        self.assertEqual(len(test), 1)
        self.assertListEqual(list(test['SerieID']), [4])

    def test_evaluate_model(self):
        # Modèle à tester
        model = SVC(kernel='linear')
        
        # Données simulées pour l'entraînement et le test
        X_train = np.array([[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]])
        y_train = np.array([1, 0, 1])
        X_test = np.array([[0.1, 0.2], [0.5, 0.6]])
        y_test = np.array([1, 1])

        # Test de la fonction
        trained_model = evaluate_model(model, X_train, y_train, X_test, y_test)

        # Vérification du type du modèle
        self.assertIsInstance(trained_model, SVC)

    @patch('services.Recommendation.Retrieve_Notes_per_Serie')
    @patch('services.Recommendation.retrieve_subtitles_from_bdd')
    @patch('utilis.bddUtilis.recommendationToSQL')
    def test_ProcessRecommendationFull(self, mock_recommendationToSQL, mock_retrieve_subtitles, mock_retrieve_notes):
        # Mock des données
        mock_retrieve_notes.return_value = self.evaluations
        mock_retrieve_subtitles.return_value = self.subtitles
        mock_recommendationToSQL.return_value = "Success"

        # Mock de la connexion
        mock_conn = MagicMock()

        # Test de la fonction
        ProcessRecommendationFull(mock_conn, userID=1)

        # Vérification des appels des mocks
        mock_retrieve_notes.assert_called_once_with(mock_conn, 1)
        mock_retrieve_subtitles.assert_called_once_with(mock_conn)

    @patch('services.Recommendation.RetrievePickleObject')
    def test_getRecommendation(self, mock_RetrievePickleObject):
        # Mock des données de la base
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        # Simuler une recommandation présente
        mock_cursor.fetchone.return_value = [b'pickled_data']
        mock_RetrievePickleObject.return_value = ['Serie A', 'Serie B']

        # Test de la fonction
        result = getRecommendation(userID=1, connection=mock_conn)

        # Assertions
        self.assertEqual(result, ['Serie A', 'Serie B'])

        # Simuler une absence de recommandation
        mock_cursor.fetchone.return_value = [None]
        result = getRecommendation(userID=2, connection=mock_conn)
        self.assertEqual(result, "No recommendation found for this user.")

if __name__ == '__main__':
    unittest.main()
