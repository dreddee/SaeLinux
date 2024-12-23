import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

# Import des fonctions 
from services.Search import CreateVectoriserModel, tfidf_search_for_terms, FullSearch

class TestTfidfModule(unittest.TestCase):

    def setUp(self):
        # Simulated subtitles data with 'Vectorised' column
        self.documentsDF = pd.DataFrame({
            'idSub': [1, 2, 3],
            'SerieID': [101, 102, 103],
            'Fullname': ['Serie A', 'Serie B', 'Serie C'],
            'content': ['this is a test', 'another test document', 'one more test'],
            'Vectorised': [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]]  # Dummy vectorized data
        })

        self.vectorizer = TfidfVectorizer()
        self.tfidf_matrix = self.vectorizer.fit_transform(self.documentsDF['content'])
        self.df_tfidf = pd.DataFrame(
            self.tfidf_matrix.toarray(), 
            index=self.documentsDF['idSub'], 
            columns=self.vectorizer.get_feature_names_out()
        )

        self.id_to_series_info = {
            row['idSub']: (row['Fullname'], row['SerieID']) for _, row in self.documentsDF.iterrows()
        }

    @patch('services.Search.retrieve_subtitles_from_bdd')
    def test_CreateVectoriserModel(self, mock_retrieve_subtitles):
        # Mock database retrieval
        mock_retrieve_subtitles.return_value = self.documentsDF

        # Test the function
        conn_mock = MagicMock()
        df_tfidf, id_to_series_info = CreateVectoriserModel(conn_mock)

        # Assertions
        self.assertEqual(len(df_tfidf), len(self.documentsDF))
        self.assertEqual(df_tfidf.shape[1], len(self.vectorizer.get_feature_names_out()))
        self.assertEqual(id_to_series_info, self.id_to_series_info)

    def test_tfidf_search_for_terms(self):
        # Test with terms that exist
        terms = ['test', 'document']
        result = tfidf_search_for_terms(self.df_tfidf, terms)

        self.assertIsInstance(result, pd.Series)
        self.assertGreater(len(result), 0)

        # Test with terms that do not exist
        terms = ['nonexistent', 'words']
        result = tfidf_search_for_terms(self.df_tfidf, terms)

        self.assertIsInstance(result, str)
        self.assertEqual(result, "None of the terms are present in the documents.")

    def test_FullSearch(self):
        recherche = ['test', 'document']
        n = 2

        # Test with valid terms
        result = FullSearch(self.df_tfidf, self.id_to_series_info, recherche, n)

        self.assertIsInstance(result, list)
        self.assertLessEqual(len(result), n)

        # Test with no matching terms
        recherche = ['nonexistent', 'words']
        result = FullSearch(self.df_tfidf, self.id_to_series_info, recherche, n)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

if __name__ == '__main__':
    unittest.main()
