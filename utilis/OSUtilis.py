def ouverture_fichier(nom):
    with open(nom, 'r', encoding='utf-8') as fichier:
        contenu = fichier.read()
    return(contenu)