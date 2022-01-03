# spotify-playlist-randomizer
## Introduction
Spotify Playlist Randomizer is a Flask web app leveraging the Spotify API to permanently randomize the order of playlists owned by an authorized user. The functionality of this is different than the functionality of the Spotify shuffle button because it changs the inherent order of the playlist instead of playing a random track at playback. <br /> <br />
The app prompts the user to login through the Spotify authorization page. Once successfully authorized using the OAuth code flow, the app uses the acquired token to request the list of playlists owned by a user. These are shown to a user in a drop down menu. Once a playlist is selected and the user clicks randomize, the app will request the playlist contents, randomize them, and update the contents of the playlist.
## Built With
* Flask
* Spotify API 
* OAuth 2.0 with PKCE Extension
* Python Requests
## Installation and Use
This Repo can be cloned and dependencies can be installed using:
```sh
pip install -r requirements.txt
```
The app can be acessed at localhost:5000 with:
```sh
python main.py
```

However, in order to access the functionality of the app, you would need to create your own Spotify Developer account and acquire your own CLIENT_ID and CLIENT_SECRET, as well as configuring the authorization code flow REDIRECT_URI on the developer dashboard and writing code to instantiate FLASK_SECRET. This information would be stored in config.py. <br /><br />
The app will be hosted in the near future and a link will be posted here.
## Acknowledgments
The authorization code flow was adapted from https://github.com/lucaoh21/Spotify-Discover-2.0. Thanks for pointing me in the right direction.
#### Other python libraries used:
* random
* time
* string
* base64
* json
