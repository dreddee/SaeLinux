import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import pickle
import base64
from mysql.connector import connect, Error
from utilis.bddUtilis import (
    getConnection, retrieve_subtitles_from_bdd, SetPickleObject, RetrievePickleObject,
    getSerie, upsert_evaluation, Retrieve_Notes_per_Serie, recommendationToSQL
)


class TestSQLFunctions(unittest.TestCase):

    @patch("utilis.bddUtilis.mysql.connector.connect")
    def test_getConnection(self, mock_connect):
        # Mock MySQL connection
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        conn = getConnection(host="localhost", user="test_user", password="test_pass")
        
        mock_connect.assert_called_once_with(
            host="localhost",
            user="test_user",
            password="test_pass",
            port="3306",
            database="saeserie",
            charset="utf8mb4"
        )
        self.assertEqual(conn, mock_conn)

    @patch("utilis.bddUtilis.pd.read_sql_query")
    def test_retrieve_subtitles_from_bdd(self, mock_read_sql_query):
        # Mock SQL query result
        mock_df = pd.DataFrame({
            'idSub': [1, 2],
            'SerieID': [101, 102],
            'Fullname': ['Serie A', 'Serie B'],
            'content': ['Test content', 'Another content'],
            'Vectorised': [SetPickleObject([0.1, 0.2]), SetPickleObject([0.3, 0.4])]
        })
        mock_read_sql_query.return_value = mock_df

        # Mock connection
        mock_conn = MagicMock()

        # Test function
        result = retrieve_subtitles_from_bdd(mock_conn)

        # Assertions
        self.assertEqual(len(result), 2)
        self.assertTrue("Vectorised" in result.columns)
        self.assertTrue(isinstance(result["Vectorised"][0], list))

    def test_SetPickleObject(self):
        obj = [1, 2, 3]
        encoded = SetPickleObject(obj)
        self.assertIsInstance(encoded, str)

    def test_RetrievePickleObject(self):
        obj = [1, 2, 3]
        encoded = SetPickleObject(obj)
        decoded = RetrievePickleObject(encoded)
        self.assertEqual(obj, decoded)

    @patch("utilis.bddUtilis.mysql.connector.connect")
    def test_getSerie(self, mock_connect):
        # Mock cursor behavior
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"SerieID": 101, "Fullname": "Serie A", "Note": 4.5}

        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        result = getSerie(mock_conn, userID=1, serieID=101)

        # Assertions
        self.assertEqual(result["SerieID"], 101)
        self.assertEqual(result["Fullname"], "Serie A")
        self.assertEqual(result["Note"], 4.5)

    @patch("utilis.bddUtilis.mysql.connector.connect")
    def test_upsert_evaluation(self, mock_connect):
        # Mock connection and cursor
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Test function
        upsert_evaluation(mock_conn, id_evaluation=1, note=5, commentaire="Great!", id_serie=101)

        # Assertions
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()

    @patch("utilis.bddUtilis.pd.read_sql_query")
    def test_Retrieve_Notes_per_Serie(self, mock_read_sql_query):
        # Mock SQL query result
        mock_df = pd.DataFrame({
            'SerieID': [101, 102],
            'Fullname': ['Serie A', 'Serie B'],
            'Vectorised': [SetPickleObject([0.1, 0.2]), SetPickleObject([0.3, 0.4])],
            'Language': ['EN', 'FR'],
            'Note': [4.5, 3.8]
        })
        mock_read_sql_query.return_value = mock_df

        # Mock connection
        mock_conn = MagicMock()

        # Test function
        result = Retrieve_Notes_per_Serie(mock_conn, id_utilisateur=1)

        # Assertions
        self.assertEqual(len(result), 2)
        self.assertIn("Language", result.columns)

    @patch("utilis.bddUtilis.mysql.connector.connect")
    def test_recommendationToSQL(self, mock_connect):
        # Mock connection and cursor
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Test function
        result = recommendationToSQL(mock_conn, Recommendation=[1, 2, 3], userID=1)

        # Assertions
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        self.assertEqual(result, "Recommendation updated successfully.")


if __name__ == "__main__":
    unittest.main()
