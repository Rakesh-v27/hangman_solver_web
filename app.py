import time
import string
import re
import pandas as pd
from flask import Flask, render_template, request, session, redirect, url_for, send_from_directory



# Import helper functions from hangman_solver.py
from hangman_solver import get_letter_frequencies, filter_titles, movie_list_function

# Load your movie dataset (ensure movies.csv is in the same directory)
movies = pd.read_csv('movies.csv', usecols=["primaryTitle"])

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


@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/game', methods=['GET', 'POST'])
def game():
    # Initialize session variables if they do not exist
    if 'life' not in session or session.get('life') is None:
        session['life'] = 10
    if 'current_pattern' not in session or session.get('current_pattern') is None:
        return redirect(url_for('index'))
    if 'not_in_list' not in session or session.get('not_in_list') is None:
        session['not_in_list'] = []
    if 'word_lengths' not in session or session.get('word_lengths') is None:
        return redirect(url_for('index'))
    if 'flag' not in session or session.get('flag') is None:
        session['flag'] = 0

    # Retrieve and enforce proper types from the session
    try:
        life = int(session.get('life', 10))
    except (TypeError, ValueError):
        session['life'] = 10
        life = 10

    current_pattern = session.get('current_pattern', '')
    not_in_list = session.get('not_in_list', [])
    word_lengths = session.get('word_lengths', [])
    try:
        flag = int(session.get('flag', 0))
    except (TypeError, ValueError):
        session['flag'] = 0
        flag = 0

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

    # If only one candidate remains, record it as the final guess.
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
        user_answer = request.form.get('user_answer', '').strip().lower()
        if user_answer == 'y':
            # If correct, go to positions route to update pattern.
            return redirect(url_for('positions'))
        else:
            # Wrong guess: update life and record the guess.
            session['life'] = max(0, life - 1)
            not_in_list.append(guess_letter)
            session['not_in_list'] = not_in_list
            return redirect(url_for('game'))

    return render_template('game.html', current_pattern=current_pattern, guess_letter=guess_letter, life=life, candidate_count=candidate_count)

@app.route('/positions', methods=['GET', 'POST'])
def positions():
    if request.method == 'GET':
        # Retrieve word lengths from session to dynamically render inputs.
        word_lengths = session.get('word_lengths', [])
        return render_template('positions.html', word_lengths=word_lengths)
    
    # For POST: Process each word's input from separate fields.
    word_lengths = session.get('word_lengths', [])
    current_pattern = session.get('current_pattern', '')
    guess_letter = session.get('guess_letter', '')
    
    positions_by_word = []
    # Expect input fields named positions_0, positions_1, ... (one per word)
    for i in range(len(word_lengths)):
        input_val = request.form.get(f'positions_{i}', '').strip()
        if input_val == "":
            # No positions indicated for this word.
            positions_by_word.append([])
        else:
            try:
                # Split by commas and convert to integers.
                positions = [int(x.strip()) for x in input_val.split(',') if x.strip() != ""]
            except ValueError:
                session['error'] = f"Invalid input for word {i+1}. Please enter valid numbers."
                return redirect(url_for('positions'))
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