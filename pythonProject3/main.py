import numpy as np
from sklearn.neighbors import NearestNeighbors
from sklearn.decomposition import NMF
from db_connection import get_connection
from get_rated_movies import get_rated_movies


def get_data_from_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Oceny")
    ratings = cursor.fetchall()

    cursor.execute("SELECT * FROM Filmy")
    movies = cursor.fetchall()

    cursor.execute("SELECT * FROM Uzytkownicy")
    users = cursor.fetchall()

    conn.close()

    return ratings, movies, users


def get_user_ratings_count(user_id):
    """Zliczamy, ile ocen użytkownik wystawił"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM Oceny WHERE user_id = %s", (user_id,))
    ratings_count = cursor.fetchone()[0]

    conn.close()

    return ratings_count


def recommend_using_knn(user_id, k=5):
    """Rekomendacja przy użyciu algorytmu KNN dla nowych użytkowników"""
    ratings, movies, users = get_data_from_db()

    user_movie_matrix = np.zeros((len(users), len(movies)))

    for rating in ratings:
        user_index = rating[0] - 1
        movie_index = rating[1] - 1
        user_movie_matrix[user_index][movie_index] = rating[2]

    knn = NearestNeighbors(metric='cosine', algorithm='brute')
    knn.fit(user_movie_matrix)

    distances, indices = knn.kneighbors(user_movie_matrix[user_id - 1].reshape(1, -1), n_neighbors=k + 1)

    recommendations = []
    for i in range(1, len(distances.flatten())):
        similar_user_id = indices.flatten()[i]
        similar_user_ratings = user_movie_matrix[similar_user_id]

        for movie_id, rating in enumerate(similar_user_ratings):
            if rating > 4.0 and user_movie_matrix[user_id - 1][movie_id] == 0:
                recommendations.append(movies[movie_id][1])

    return recommendations


def recommend_using_matrix_factorization(user_id):
    """Rekomendacja przy użyciu Faktoryzacji Macierzy (NMF)"""
    ratings, movies, users = get_data_from_db()

    user_movie_matrix = np.zeros((len(users), len(movies)))

    for rating in ratings:
        user_index = rating[0] - 1
        movie_index = rating[1] - 1
        user_movie_matrix[user_index][movie_index] = rating[2]

    # Faktoryzacja Macierzy (NMF)
    nmf = NMF(n_components=15, init='random', random_state=42, max_iter=500)
    user_features = nmf.fit_transform(user_movie_matrix)
    movie_features = nmf.components_

    user_profile = user_features[user_id - 1]
    recommendations_scores = np.dot(user_profile, movie_features)

    recommendations = []
    user_rated_movies = user_movie_matrix[user_id - 1]

    for movie_id, score in enumerate(recommendations_scores):
        if user_rated_movies[movie_id] == 0:
            recommendations.append((movies[movie_id][1], score))

    recommendations = sorted(recommendations, key=lambda x: x[1], reverse=True)

    return [movie for movie, score in recommendations[:10]]


def hybrid_recommendation_system(user_id):
    """Hybrydowy system rekomendacji z informacją o użytym algorytmie"""
    ratings_count = get_user_ratings_count(user_id)

    if ratings_count <= 2:
        # Jeśli użytkownik ma mniej niż 3 oceny, używamy KNN
        recommendations = recommend_using_knn(user_id)
        algorithm_used = "KNN"
    else:
        # Jeśli użytkownik ma więcej ocen, używamy Faktoryzacji Macierzy
        recommendations = recommend_using_matrix_factorization(user_id)
        algorithm_used = "Matrix Factorization (NMF)"

    return recommendations, algorithm_used


def add_to_favorites(user_id, movie_id):
    """Dodaje film do ulubionych dla użytkownika."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Ulubione WHERE user_id = %s AND movie_id = %s", (user_id, movie_id))
    result = cursor.fetchone()

    if result:
        print("Film jest już w ulubionych.")
    else:
        cursor.execute("INSERT INTO Ulubione (user_id, movie_id) VALUES (%s, %s)", (user_id, movie_id))
        conn.commit()
        print(f"Film o ID {movie_id} został dodany do ulubionych dla użytkownika {user_id}.")

    conn.close()


def get_favorites(user_id):
    """Zwraca listę ulubionych filmów użytkownika."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""SELECT f.title 
                      FROM Ulubione u
                      JOIN Filmy f ON u.movie_id = f.id
                      WHERE u.user_id = %s""", (user_id,))

    favorites = cursor.fetchall()
    conn.close()

    return [f[0] for f in favorites]


def get_all_movies():
    """Zwraca wszystkie filmy z bazy danych."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Filmy")
    movies = cursor.fetchall()

    conn.close()

    return movies


def rate_movie(user_id, movie_id, rating):
    """Dodaje ocenę filmu do bazy danych."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Oceny WHERE user_id = %s AND movie_id = %s", (user_id, movie_id))
    result = cursor.fetchone()

    if result:
        print("Film został już oceniony przez tego użytkownika.")
    else:
        cursor.execute("INSERT INTO Oceny (user_id, movie_id, rating) VALUES (%s, %s, %s)", (user_id, movie_id, rating))
        conn.commit()
        print(f"Film o ID {movie_id} został oceniony na {rating} przez użytkownika {user_id}.")

    conn.close()


if __name__ == "__main__":
    # Wybór użytkownika
    user_id = int(input("Podaj swoje ID użytkownika: "))

    while True:
        print("\nWybierz opcję:")
        print("1. Przeglądaj wszystkie filmy")
        print("2. Ocen film")
        print("3. Dodaj film do ulubionych")
        print("4. Uzyskaj rekomendacje")
        print("5. Wyświetl ulubione filmy")
        print("6. Wyjdź")

        option = int(input("Wybierz opcję (1-6): "))

        if option == 1:
            movies = get_all_movies()
            print("\nWszystkie filmy w bibliotece:")
            for movie in movies:
                print(f"ID: {movie[0]}, Tytuł: {movie[1]}, Gatunek: {movie[2]}")

        elif option == 2:
            movie_id = int(input("Podaj ID filmu do oceny: "))
            rating = float(input("Podaj ocenę (1-5): "))
            rate_movie(user_id, movie_id, rating)

        elif option == 3:
            movie_id = int(input("Podaj ID filmu do dodania do ulubionych: "))
            add_to_favorites(user_id, movie_id)

        elif option == 4:
            recommendations, algorithm_used = hybrid_recommendation_system(user_id)
            print(f"Rekomendacje dla użytkownika {user_id} (algorytm: {algorithm_used}):")
            for movie in recommendations:
                print(movie)

        elif option == 5:
            favorites = get_favorites(user_id)
            print(f"Ulubione filmy użytkownika {user_id}: {favorites}")

        elif option == 6:
            print("Dziękujemy za korzystanie z systemu rekomendacji!")
            break

        else:
            print("Nieprawidłowa opcja. Spróbuj ponownie.")
