import string
import pandas as pd
import re


try:
    movies = pd.read_csv("movies.csv")
    if "primaryTitle" not in movies.columns:
        raise ValueError("CSV file must contain a 'primaryTitle' column")
except FileNotFoundError:
    print("Error: movies.csv not found.")
    movies = pd.DataFrame(columns=["primaryTitle"])  
except Exception as e:
    print(f"Error loading movies.csv: {e}")
    movies = pd.DataFrame(columns=["primaryTitle"]) 

def get_letter_frequencies(movie_list):
    """
    Given a list of movie titles,
    returns a dictionary mapping each letter to the percentage of titles
    that contain that letter at least once. The dictionary is sorted in descending
    order of percentage.
    """
    total_movies = len(movie_list)
    if total_movies == 0:
        return {}
    
    normalized_titles = [title.lower() for title in movie_list]
    alphabet = set(string.ascii_lowercase)
    percentages = {}
    for letter in alphabet:
        count = sum(1 for t in normalized_titles if letter in t)
        percentages[letter] = (count / total_movies) * 100
    sorted_percentages = dict(sorted(percentages.items(), key=lambda x: x[1], reverse=True))
    return sorted_percentages

def filter_titles(titles, desired_word_count, not_in):
    """
    Filters a list of titles, returning only those that:
    Have exactly `desired_word_count` words and do not contain any letter from the 'not_in' list.
    
    Parameters:
    titles: The list of movie titles.
    desired_word_count: The exact number of words required.
    not_in: Letters that must not appear in the title.
        
    Returns: The filtered list of titles.
    """
    filtered = []
    for title in titles:
        if len(title.split()) != desired_word_count:
            continue

        lower_title = title.lower()
        if any(letter in lower_title for letter in not_in):
            continue
        
        filtered.append(title)
    return filtered

def movie_list_function(user_pattern):
    """
    Given a user pattern (ex - "___e.____e"), this function normalises the movie titles
    from the global 'movies' DataFrame and returns a list of titles matching the pattern.
    
    The pattern assumes:
    Underscores ('_') represent unknown letters.
    A dot ('.') indicates a word separator.
    
    The function converts underscores to '.' (regex wildcard) and uses a whitespace pattern for the dot.
    """
    if 'normalized_title' not in movies.columns:
        movies['normalized_title'] = movies['primaryTitle'].str.lower().str.strip()
    
    parts = user_pattern.split('.')
    word_patterns = [part.replace('_', '.') for part in parts]
    regex_pattern = "^" + r"\s".join(word_patterns) + "$"
    print("Regex pattern:", regex_pattern) 
    
    matching_movies = movies[movies['normalized_title'].str.fullmatch(regex_pattern, na=False)]
    matching_movie_list = matching_movies['primaryTitle'].tolist()
    return matching_movie_list
