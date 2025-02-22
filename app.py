import time
import string
import re
import pandas as pd
from flask import Flask, render_template, request, session, redirect, url_for, send_from_directory



from hangman_solver import get_letter_frequencies, filter_titles, movie_list_function

movies = pd.read_csv('movies.csv', usecols=["primaryTitle"])


app = Flask(__name__)
app.secret_key = "1@2@3@4@5"


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        word_lengths_input = request.form.get('word_lengths')
        try:
            word_lengths = [int(x.strip()) for x in word_lengths_input.split(',')]
        except ValueError:
            error = "Invalid input. Please enter numbers separated by commas."
            return render_template('index.html', error=error)
        
        current_pattern_words = ['_' * length for length in word_lengths]
        current_pattern = '.'.join(current_pattern_words)
        
        session['word_lengths'] = word_lengths
        session['current_pattern'] = current_pattern
        session['life'] = 10
        session['not_in_list'] = []
        session['flag'] = 0 
        session.pop('guess_letter', None)
        session.pop('final_guess', None)
        
        return redirect(url_for('game'))
    return render_template('index.html')


@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/game', methods=['GET', 'POST'])
def game():
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

    if life <= 0 or ('_' not in current_pattern) or flag == 1:
        final_guess = session.get('final_guess', None)
        return render_template('game_over.html', current_pattern=current_pattern, life=life, final_guess=final_guess)


    candidate_list = movie_list_function(current_pattern)

    filtered_candidates = filter_titles(candidate_list, len(word_lengths), not_in_list)
    candidate_count = len(filtered_candidates)

    freq_dict = get_letter_frequencies(filtered_candidates)

    if len(set(filtered_candidates)) == 1:
        session['flag'] = 1
        session['final_guess'] = list(set(filtered_candidates))[0]
        return redirect(url_for('game'))

    guess_letter = None
    for letter in freq_dict.keys():
        if letter not in current_pattern and letter not in not_in_list:
            guess_letter = letter
            break

    if guess_letter is None:
        return render_template('game_over.html', message="No new letters to guess.", current_pattern=current_pattern, life=life)

    session['guess_letter'] = guess_letter

    if request.method == 'POST':
        user_answer = request.form.get('user_answer', '').strip().lower()
        if user_answer == 'y':
            return redirect(url_for('positions'))
        else:
            session['life'] = max(0, life - 1)
            not_in_list.append(guess_letter)
            session['not_in_list'] = not_in_list
            return redirect(url_for('game'))

    return render_template('game.html', current_pattern=current_pattern, guess_letter=guess_letter, life=life, candidate_count=candidate_count)

@app.route('/positions', methods=['GET', 'POST'])
def positions():
    if request.method == 'GET':
        word_lengths = session.get('word_lengths', [])
        return render_template('positions.html', word_lengths=word_lengths)
    
    word_lengths = session.get('word_lengths', [])
    current_pattern = session.get('current_pattern', '')
    guess_letter = session.get('guess_letter', '')
    
    positions_by_word = []
    for i in range(len(word_lengths)):
        input_val = request.form.get(f'positions_{i}', '').strip()
        if input_val == "":
            positions_by_word.append([])
        else:
            try:
                positions = [int(x.strip()) for x in input_val.split(',') if x.strip() != ""]
            except ValueError:
                session['error'] = f"Invalid input for word {i+1}. Please enter valid numbers."
                return redirect(url_for('positions'))
            positions_by_word.append(positions)
    
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


if __name__ == '__main__':
    app.run(debug=True)