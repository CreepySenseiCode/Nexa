"""Données FAQ pour le chatbot d'aide."""

FAQ_DATA = [
    {
        "question": "Bienvenue ! Que puis-je faire en mode Vendeur ?",
        "reponse": (
            "En mode Vendeur, vous avez accès aux fonctions essentielles :\n\n"
            "• Créer et modifier des fiches clients\n"
            "• Enregistrer des ventes\n"
            "• Rechercher des clients\n"
            "• Vérifier et appliquer des codes promo\n"
            "• Consulter les produits\n"
            "• Gérer vos tâches et sous-tâches\n"
            "• Consulter le calendrier\n\n"
            "Pour accéder aux fonctions avancées (emailing, statistiques, paramètres), "
            "demandez le mot de passe administratif à votre responsable."
        ),
        "mots_cles": [
            "vendeur",
            "mode",
            "bienvenue",
            "fonctions",
            "accueil",
            "faire",
            "guide",
            "accès",
        ],
        "visibility": "vendeur_only",
    },
    {
        "question": "Comment créer un nouveau client ?",
        "reponse": (
            "1. Allez dans l'onglet Client\n"
            "2. Remplissez les champs obligatoires (Nom et Prénom minimum)\n"
            "3. Ajoutez les informations supplémentaires si nécessaire\n"
            "4. Cliquez sur Enregistrer\n\n"
            "💡 Les champs marqués d'une astérisque (*) sont obligatoires."
        ),
        "mots_cles": [
            "client",
            "créer",
            "nouveau",
            "ajouter",
            "fiche",
            "enregistrer",
            "création",
        ],
        "visibility": "all",
    },
    {
        "question": "Comment enregistrer une vente ?",
        "reponse": (
            "1. Allez dans l'onglet Vente\n"
            "2. Recherchez et sélectionnez le client\n"
            "3. Sélectionnez le produit acheté\n"
            "4. Indiquez la quantité et vérifiez le prix\n"
            "5. Cliquez sur Enregistrer la vente\n\n"
            "💡 Si le produit n'existe pas, vous pouvez le créer directement depuis cet onglet."
        ),
        "mots_cles": [
            "vente",
            "enregistrer",
            "vendre",
            "produit",
            "achat",
            "transaction",
            "commande",
        ],
        "visibility": "all",
    },
    {
        "question": "Comment utiliser un code promo ?",
        "reponse": (
            "Pour vérifier un code :\n"
            "1. Allez dans l'onglet Codes promo → Rechercher\n"
            "2. Entrez le code et cliquez sur Vérifier\n\n"
            "Pour l'appliquer à une vente :\n"
            "1. Dans l'onglet Vente, sélectionnez le client et le produit\n"
            "2. Entrez le code dans le champ Code promo\n"
            "3. Cliquez sur Appliquer — le prix sera automatiquement recalculé\n\n"
            "💡 Les codes peuvent avoir des limitations (expiration, usage unique, etc.)."
        ),
        "mots_cles": [
            "code",
            "promo",
            "réduction",
            "promotion",
            "discount",
            "appliquer",
            "vérifier",
            "coupon",
        ],
        "visibility": "all",
    },
    {
        "question": "Comment rechercher un client ?",
        "reponse": (
            "1. Allez dans l'onglet Recherche\n"
            "2. Tapez dans la barre de recherche (nom, prénom, email ou téléphone)\n"
            "3. Les résultats apparaissent en temps réel sous forme de cartes\n"
            "4. Cliquez sur une carte pour afficher le profil complet\n\n"
            '💡 Vous pouvez combiner plusieurs mots (ex : "Jean Paris").'
        ),
        "mots_cles": [
            "rechercher",
            "chercher",
            "trouver",
            "client",
            "recherche",
            "barre",
            "profil",
        ],
        "visibility": "all",
    },
    {
        "question": "Comment gérer mes tâches ?",
        "reponse": (
            "1. Allez dans l'onglet Tâches\n"
            "2. Créez une tâche avec le bouton Création\n"
            "3. Définissez une priorité, une catégorie et une échéance\n"
            "4. Les sous-tâches permettent de décomposer une tâche complexe\n"
            "5. Cochez une tâche pour la marquer comme terminée\n\n"
            "💡 Cliquez sur le titre ou la description d'une tâche dans la liste pour la modifier directement."
        ),
        "mots_cles": [
            "tâche",
            "taches",
            "gérer",
            "créer",
            "priorité",
            "sous-tâche",
            "deadline",
            "échéance",
            "todo",
        ],
        "visibility": "all",
    },
    {
        "question": "Comment utiliser le calendrier ?",
        "reponse": (
            "Le calendrier affiche vos tâches, commandes et événements :\n\n"
            "• Vue Mois : aperçu général avec badges colorés\n"
            "• Vue Semaine : planning horaire sur 7 jours\n"
            "• Vue Jour : timeline détaillée heure par heure\n"
            "• Vue Année : vue d'ensemble des 12 mois\n\n"
            "Cliquez sur un événement pour voir sa fiche détaillée.\n"
            "Cliquez sur un jour pour passer en vue Jour."
        ),
        "mots_cles": [
            "calendrier",
            "agenda",
            "vue",
            "mois",
            "semaine",
            "jour",
            "événement",
            "planning",
            "date",
        ],
        "visibility": "all",
    },
    {
        "question": "Quelle est la différence entre mode Vendeur et mode Patron ?",
        "reponse": (
            "Mode Vendeur (par défaut) :\n"
            "• Créer/modifier des clients\n"
            "• Enregistrer des ventes\n"
            "• Rechercher des clients\n"
            "• Vérifier des codes promo\n"
            "• Gérer les tâches et le calendrier\n\n"
            "Mode Patron (avec mot de passe) :\n"
            "• Tout le mode Vendeur +\n"
            "• Emailing et boîte de réception\n"
            "• Statistiques de vente\n"
            "• Création de codes promo\n"
            "• Gestion des produits\n"
            "• Paramètres de l'application\n\n"
            "💡 Cliquez sur le cadenas pour basculer entre les modes."
        ),
        "mots_cles": [
            "différence",
            "vendeur",
            "patron",
            "admin",
            "mode",
            "accès",
            "comparaison",
            "rôle",
        ],
        "visibility": "all",
    },
    {
        "question": "Comment accéder au mode Patron ?",
        "reponse": (
            "1. Survolez la barre latérale pour la déployer\n"
            "2. Cliquez sur le cadenas en bas de la barre\n"
            "3. Entrez le mot de passe administratif\n\n"
            "Si vous n'avez pas le mot de passe, demandez-le à votre responsable.\n\n"
            "Mot de passe oublié ?\n"
            "• Après 3 tentatives échouées → un indice s'affiche\n"
            "• Après 5 tentatives → un email de récupération peut être envoyé"
        ),
        "mots_cles": [
            "patron",
            "admin",
            "accéder",
            "mode",
            "cadenas",
            "connexion",
            "mot de passe",
            "login",
        ],
        "visibility": "vendeur_only",
    },
    {
        "question": "Comment définir ou modifier le mot de passe patron ?",
        "reponse": (
            "Première utilisation :\n"
            "Au premier lancement, l'application vous propose de définir un mot de passe.\n\n"
            "Pour modifier le mot de passe :\n"
            "1. Connectez-vous en mode Patron\n"
            "2. Allez dans Paramètres → Section Sécurité\n"
            "3. Cliquez sur Modifier le mot de passe\n\n"
            "💡 Le mot de passe doit contenir au moins 8 caractères, "
            "1 majuscule, 1 chiffre et 1 caractère spécial."
        ),
        "mots_cles": [
            "mot de passe",
            "password",
            "définir",
            "modifier",
            "changer",
            "sécurité",
            "patron",
            "reset",
        ],
        "visibility": "admin_only",
    },
    {
        "question": "J'ai oublié mon mot de passe patron, que faire ?",
        "reponse": (
            "Si vous avez défini un indice :\n"
            "Après 3 tentatives échouées, l'indice s'affichera automatiquement.\n\n"
            "Si vous avez un email de récupération enregistré :\n"
            "Après 5 tentatives, vous pourrez demander une réinitialisation par email.\n\n"
            "En dernier recours :\n"
            "Contactez l'administrateur système qui peut réinitialiser le mot de passe "
            "via le script reset_password.py.\n\n"
            "💡 Notez votre indice dans un endroit sûr !"
        ),
        "mots_cles": [
            "oublié",
            "oublie",
            "mot de passe",
            "password",
            "récupération",
            "reset",
            "indice",
            "perdu",
        ],
        "visibility": "admin_only",
    },
    {
        "question": "Comment créer un code promo ?",
        "reponse": (
            "1. Connectez-vous en mode Patron\n"
            "2. Allez dans l'onglet Codes promo → Création\n"
            "3. Remplissez les informations :\n"
            "   • Code (ex : NOEL2026)\n"
            "   • Pourcentage de réduction\n"
            "   • Description et dates de validité\n"
            "   • Type d'utilisation (illimité, limité globalement, limité par client)\n"
            "4. Cliquez sur Créer le code\n\n"
            "💡 Les codes sont automatiquement convertis en majuscules."
        ),
        "mots_cles": [
            "code",
            "promo",
            "créer",
            "création",
            "réduction",
            "promotion",
            "patron",
            "nouveau code",
        ],
        "visibility": "admin_only",
    },
    {
        "question": "Comment voir les statistiques de vente ?",
        "reponse": (
            "1. Connectez-vous en mode Patron\n"
            "2. Allez dans l'onglet Statistiques\n"
            "3. Choisissez une période (aujourd'hui, ce mois, cette année...)\n"
            "4. Consultez les graphiques interactifs\n\n"
            "💡 Vous pouvez exporter les statistiques en PDF ou CSV."
        ),
        "mots_cles": [
            "statistiques",
            "stats",
            "vente",
            "graphique",
            "chiffre",
            "export",
            "patron",
            "rapport",
            "données",
        ],
        "visibility": "admin_only",
    },
    {
        "question": "Comment gérer les emails et l'emailing ?",
        "reponse": (
            "L'onglet Emails regroupe toutes vos communications :\n\n"
            "• Réception : vos emails reçus\n"
            "• Envoyés : historique des emails envoyés\n"
            "• Brouillons : emails en cours de rédaction\n"
            "• Templates : modèles réutilisables\n"
            "• Rédiger : composer un nouvel email\n\n"
            "💡 Utilisez le bouton + dans l'onglet Rédiger pour ouvrir "
            "plusieurs brouillons en parallèle."
        ),
        "mots_cles": [
            "email",
            "mail",
            "emailing",
            "envoyer",
            "boîte",
            "template",
            "modèle",
            "rédiger",
            "réception",
        ],
        "visibility": "admin_only",
    },
    {
        "question": "Que signifie 'Profil complet' / 'Profil incomplet' ?",
        "reponse": (
            "Un profil est considéré comme complet si tous les champs obligatoires "
            "(définis dans les Paramètres) sont renseignés.\n\n"
            "Pourquoi c'est important ?\n"
            "• Meilleure qualité des données\n"
            "• Emails plus personnalisés\n"
            "• Statistiques plus précises\n\n"
            "💡 Vous pouvez personnaliser quels champs sont obligatoires dans les Paramètres."
        ),
        "mots_cles": [
            "profil",
            "complet",
            "incomplet",
            "champ",
            "obligatoire",
            "qualité",
            "données",
            "badge",
        ],
        "visibility": "admin_only",
    },
]
