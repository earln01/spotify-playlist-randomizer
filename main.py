import re
import spotipy
from flask import  Flask, render_template, redirect, request, session, make_response,session,redirect
from config import *
from authFuncs import *
import requests
import random


app = Flask(__name__)
app.secret_key = FLASK_SECRET

@app.route("/index")
@app.route("/")
def verify():
    return render_template('index.html', auth_url = createAuthURL(session))

@app.route('/forward', methods=['GET'])
def forward():
    return redirect(createAuthURL(session))

@app.route("/callback")
def callback():
    if request.args.get('state') != session['state_key']:
        print('State does not match', flush = True)
        session.clear()
        return redirect('index')
    if request.args.get('error'):
        print('Spotify error', flush = True)
        session.clear()
        return redirect('index')
    else:
        code = request.args.get('code')
        session.pop('state_key', None)

        tokenSuccess = getToken(code, session)

        if tokenSuccess:
            return redirect('randomize')
        else:
            return redirect('index')

@app.route("/randomize")
def randomize():
    playlists = getAllPlaylists(session)
    if not playlists:
        return render_template('noPlaylists.html')
    return render_template('randomize.html', playlists = playlists)

@app.route("/randomized", methods=['POST'])
def randomized():
    if request.method == 'POST':
        playlist = request.form['Playlists']
    for character in ['(', ')', "'"]:
        playlist = playlist.replace(character, '')

    playlistTup = playlist.split(',') 
    tracks = getAllPlaylistItems(session, playlistTup[1])
    random.shuffle(tracks)

    updateStatus = updatePlaylistItems(session, playlistTup[1], tracks)
    if updateStatus:
        return render_template('randomized.html', playlist = playlistTup[0])
    else:
        return render_template('randomizeFail.html')
    


if __name__ == "__main__":
    app.run(debug=True)