import unittest
from unittest.mock import mock_open, patch

# La fonction à tester
def ouverture_fichier(nom):
    with open(nom, 'r', encoding='utf-8') as fichier:
        contenu = fichier.read()
    return contenu

class TestOuvertureFichier(unittest.TestCase):

    @patch("builtins.open", new_callable=mock_open, read_data="Contenu du fichier simulé")
    def test_ouverture_fichier(self, mock_file):
        # Nom de fichier simulé
        nom_fichier = "fichier_test.txt"

        # Appel de la fonction
        contenu = ouverture_fichier(nom_fichier)

        # Vérifications
        mock_file.assert_called_once_with(nom_fichier, 'r', encoding='utf-8')
        self.assertEqual(contenu, "Contenu du fichier simulé")

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_ouverture_fichier_file_not_found(self, mock_file):
        # Nom de fichier inexistant
        nom_fichier = "fichier_inexistant.txt"

        # Test que l'exception est levée
        with self.assertRaises(FileNotFoundError):
            ouverture_fichier(nom_fichier)

if __name__ == "__main__":
    unittest.main()
