import string
import pandas as pd
import re


# Load the movies dataset (Ensure movies.csv is in the same directory)
try:
    movies = pd.read_csv("movies.csv")
    if "primaryTitle" not in movies.columns:
        raise ValueError("CSV file must contain a 'primaryTitle' column")
except FileNotFoundError:
    print("Error: movies.csv not found. Please ensure it exists in the project directory.")
    movies = pd.DataFrame(columns=["primaryTitle"])  # Empty DataFrame to prevent crashes.
except Exception as e:
    print(f"Error loading movies.csv: {e}")
    movies = pd.DataFrame(columns=["primaryTitle"])  # Handle unexpected errors safely.

def get_letter_frequencies(movie_list):
    """
    Given a list of movie titles (all assumed to belong to the same word-count group),
    returns a dictionary mapping each letter (a-z) to the percentage of titles
    that contain that letter at least once. The dictionary is sorted in descending
    order of percentage.
    """
    total_movies = len(movie_list)
    if total_movies == 0:
        return {}
    
    # Normalize each title to lowercase.
    normalized_titles = [title.lower() for title in movie_list]
    alphabet = set(string.ascii_lowercase)
    percentages = {}
    for letter in alphabet:
        count = sum(1 for t in normalized_titles if letter in t)
        percentages[letter] = (count / total_movies) * 100
    # Sort the dictionary by percentage in descending order.
    sorted_percentages = dict(sorted(percentages.items(), key=lambda x: x[1], reverse=True))
    return sorted_percentages

def filter_titles(titles, desired_word_count, not_in):
    """
    Filters a list of titles, returning only those that:
      - Have exactly `desired_word_count` words.
      - Do NOT contain any letter from the `not_in` list.
    
    Parameters:
        titles (list of str): The list of movie titles.
        desired_word_count (int): The exact number of words required.
        not_in (list of str): Letters that must not appear in the title.
        
    Returns:
        list of str: The filtered list of titles.
    """
    filtered = []
    for title in titles:
        # Check if the title has the exact number of words.
        if len(title.split()) != desired_word_count:
            continue
        
        # Convert title to lowercase for case-insensitive checking.
        lower_title = title.lower()
        # Skip titles that contain any letter in the not_in list.
        if any(letter in lower_title for letter in not_in):
            continue
        
        filtered.append(title)
    return filtered

def movie_list_function(user_pattern):
    """
    Given a user pattern (e.g., "___e.____e"), this function normalizes the movie titles
    from the global 'movies' DataFrame and returns a list of titles matching the pattern.
    
    The pattern assumes:
      - Underscores ('_') represent unknown letters.
      - A literal dot ('.') indicates a word separator.
    
    The function converts underscores to '.' (regex wildcard) and uses a whitespace pattern for the dot.
    """
    # Ensure normalized titles exist.
    if 'normalized_title' not in movies.columns:
        movies['normalized_title'] = movies['primaryTitle'].str.lower().str.strip()
    
    # Split the user pattern on '.' to separate words.
    parts = user_pattern.split('.')
    # Replace underscores with '.' for regex matching.
    word_patterns = [part.replace('_', '.') for part in parts]
    # Join the word patterns with a whitespace regex (\s) and add start/end anchors.
    regex_pattern = "^" + r"\s".join(word_patterns) + "$"
    print("Regex pattern:", regex_pattern)  # Debug output
    
    # Use pandas' vectorized string matching to filter titles.
    matching_movies = movies[movies['normalized_title'].str.fullmatch(regex_pattern, na=False)]
    matching_movie_list = matching_movies['primaryTitle'].tolist()
    return matching_movie_list
