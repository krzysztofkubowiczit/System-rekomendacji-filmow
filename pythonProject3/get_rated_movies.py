import mysql.connector


def get_rated_movies(user_id):
    """Zwraca filmy ocenione przez danego użytkownika."""
    connection = None  # Inicjalizujemy zmienną na początku
    try:
        # Połączenie z bazą danych
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='movie_recommendation'
        )

        cursor = connection.cursor()

        # Zapytanie SQL do pobrania ocenionych filmów przez użytkownika
        query = """
        SELECT f.title, f.genre, o.rating
        FROM Filmy f
        JOIN Oceny o ON f.id = o.movie_id
        WHERE o.user_id = %s;
        """
        cursor.execute(query, (user_id,))

        # Pobieranie wyników
        rated_movies = cursor.fetchall()

        # Wypisywanie ocenionych filmów
        if rated_movies:
            print(f"Filmy ocenione przez użytkownika o ID {user_id}:")
            for movie in rated_movies:
                print(f"Tytuł: {movie[0]}, Gatunek: {movie[1]}, Ocena: {movie[2]}")
        else:
            print(f"Użytkownik o ID {user_id} nie ocenił jeszcze żadnych filmów.")

    except mysql.connector.Error as err:
        print(f"Błąd: {err}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
