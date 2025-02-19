import time
import string
import re
import pandas as pd
from flask import Flask, render_template, request, session, redirect, url_for

# Import helper functions from hangman_solver.py
from hangman_solver import get_letter_frequencies, filter_titles, movie_list_function

# Load your movie dataset (ensure movies.csv is in the same directory)
movies = pd.read_csv('movies.csv')

# Create the Flask app
app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Replace with a strong secret key

# Home/Setup route: User enters the word structure.
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        word_lengths_input = request.form.get('word_lengths')
        try:
            word_lengths = [int(x.strip()) for x in word_lengths_input.split(',')]
        except ValueError:
            error = "Invalid input. Please enter numbers separated by commas."
            return render_template('index.html', error=error)
        
        # Build the initial pattern (e.g., "____.____" for "4,4")
        current_pattern_words = ['_' * length for length in word_lengths]
        current_pattern = '.'.join(current_pattern_words)
        
        # Initialize game state in the session.
        session['word_lengths'] = word_lengths
        session['current_pattern'] = current_pattern
        session['life'] = 10
        session['not_in_list'] = []
        session['flag'] = 0  # flag indicates unique candidate found
        session.pop('guess_letter', None)
        session.pop('final_guess', None)
        
        return redirect(url_for('game'))
    return render_template('index.html')

# Main game route: Implements the game loop.
@app.route('/game', methods=['GET', 'POST'])
def game():
    current_pattern = session.get('current_pattern')
    life = session.get('life')
    not_in_list = session.get('not_in_list')
    word_lengths = session.get('word_lengths')
    flag = session.get('flag')
    
    # Game over conditions: solved, out of lives, or unique candidate found.
    if life <= 0 or ('_' not in current_pattern) or flag == 1:
        final_guess = session.get('final_guess', None)
        return render_template('game_over.html', current_pattern=current_pattern, life=life, final_guess=final_guess)
    
    # 1. Get candidate movies using the current pattern.
    candidate_list = movie_list_function(current_pattern)
    # 2. Filter candidates by desired word count and excluding letters that were wrong.
    filtered_candidates = filter_titles(candidate_list, len(word_lengths), not_in_list)
    candidate_count = len(filtered_candidates)
    
    # 3. Get letter frequencies from the filtered candidate list.
    freq_dict = get_letter_frequencies(filtered_candidates)
    
    # If only one candidate remains, record it as final guess.
    if len(set(filtered_candidates)) == 1:
        session['flag'] = 1
        session['final_guess'] = list(set(filtered_candidates))[0]
        return redirect(url_for('game'))
    
    # 4. Choose the next guess: first letter not already guessed.
    guess_letter = None
    for letter in freq_dict.keys():
        if letter not in current_pattern and letter not in not_in_list:
            guess_letter = letter
            break
    if guess_letter is None:
        return render_template('game_over.html', message="No new letters to guess.", current_pattern=current_pattern, life=life)
    
    session['guess_letter'] = guess_letter
    
    # Process user response on whether the guess was correct.
    if request.method == 'POST':
        user_answer = request.form.get('user_answer').strip().lower()
        if user_answer == 'y':
            # If correct, go to positions route to update pattern.
            return redirect(url_for('positions'))
        else:
            # Wrong guess: update life and record the guess.
            life -= 1
            not_in_list.append(guess_letter)
            session['life'] = life
            session['not_in_list'] = not_in_list
            return redirect(url_for('game'))
    
    return render_template('game.html', current_pattern=current_pattern, guess_letter=guess_letter, life=life, candidate_count=candidate_count)

@app.route('/positions', methods=['POST'])
def positions():
    pos_input = request.form.get('positions').strip()  # E.g., "1,2-3" or "1,,4"
    word_lengths = session.get('word_lengths')
    current_pattern = session.get('current_pattern')
    guess_letter = session.get('guess_letter')
    
    # Split on '-' to get groups for each word.
    pos_parts = pos_input.split('-')
    if len(pos_parts) != len(word_lengths):
        # Instead of rendering a separate template, you can flash an error or store it in the session.
        session['error'] = "The number of position groups does not match the number of words. Please try again."
        return redirect(url_for('game'))
    
    positions_by_word = []
    for group in pos_parts:
        group = group.strip()
        if group == "":
            positions_by_word.append([])
        else:
            try:
                positions = [int(pos.strip()) for pos in group.split(',') if pos.strip() != ""]
            except ValueError:
                session['error'] = "Invalid position input. Please enter valid numbers."
                return redirect(url_for('game'))
            positions_by_word.append(positions)
    
    # Update the current pattern with the guessed letter at the indicated positions.
    current_pattern_words = current_pattern.split('.')
    updated_words = []
    for i, positions in enumerate(positions_by_word):
        word_chars = list(current_pattern_words[i])
        for pos in positions:
            if 1 <= pos <= len(word_chars):
                word_chars[pos - 1] = guess_letter
        updated_words.append(''.join(word_chars))
    updated_pattern = '.'.join(updated_words)
    session['current_pattern'] = updated_pattern
    
    return redirect(url_for('game'))

# Run the Flask app.
if __name__ == '__main__':
    app.run(debug=True)
