from config import *
import random
import requests
import time
import string as string
import base64 
import json
import time

TOKEN_BASE = 'https://accounts.spotify.com/api/token'
AUTH_BASE = 'https://accounts.spotify.com/authorize'

"""
AUTHENTICATION: To make a request to the Spotify API, the application needs an access
token for the user. This token expires every 60 minutes. To acquire a new token, the 
refresh token can be sent to the API, which will return a new access token.
"""
"""
Creates a state key for the authorization request. State keys are used to make sure that
a response comes from the same place where the initial request was sent. This prevents attacks,
such as forgery. 
Returns: A state key (str) with a parameter specified size.
"""
def createStateKey(size):
	#https://stackoverflow.com/questions/2257441/random-string-generation-with-upper-case-letters-and-digits
	return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(size))

"""
Request initial user authorization from the spotify API and check that the return state key is a match. Return the constructed authorization URL to redirect user from the homepage.
Returns: URL for authorization redirect
"""

def createAuthURL(session):
	scope = 'playlist-modify-private playlist-modify-public playlist-read-private'
	session['state_key'] = createStateKey(15)

	auth_url = f'{AUTH_BASE}?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}&state={session["state_key"]}&scope={scope}&show_dialog=True'
	print(auth_url)

	return auth_url


"""
Create base64 authentication string as described in the Spotify Developer authentication code flow.

Returns: Authentication parameter
"""

def createAuthorization():
	return base64.urlsafe_b64encode(bytes(f"{CLIENT_ID}:{CLIENT_SECRET}", encoding = 'utf8')).decode()

"""
Get the User Id string from the authorized user. Called in getToken to store in session

Returns: tuple (String userID from Spotify API /me endpoint if success else None, error code if error else None)
"""
def getUserID(token):
	meURL = 'https://api.spotify.com/v1/me'
	headers = {"Authorization": "Bearer " + token, 'Content-Type': 'application/json'}
	response = requests.get(meURL, headers=headers)
	if response.status_code == 200:
		return (response.json()["id"], response.status_code)
	else:
		return (None, response.status_code)


"""
Requests an access token from the Spotify API. Only called if no refresh token for the
current user exists.
Returns: either [access token, refresh token, expiration time] or None if request failed
"""
def getToken(code, session):

	headers = {'Authorization': 'Basic ' + createAuthorization(), 'Accept': 'application/json', 'Content-Type': 'application/x-www-form-urlencoded'}
	body = {'code': code, 'redirect_uri': REDIRECT_URI, 'grant_type': 'authorization_code'}
	post_response = requests.post(TOKEN_BASE, headers=headers, data=body)
	res_json = post_response.json()

	# 200 code indicates access token was properly granted
	if post_response.status_code == 200:
		session['access_token'] = res_json['access_token']
		session['refresh_token'] = res_json['refresh_token']
		session['token_expiration'] = time.time() + res_json['expires_in']
		user_id, status_code = getUserID(session['access_token'])
		if user_id:
			session['user_id'] = user_id
			return True
		else:
			print('Error getting user_id from Spotify' + str(status_code), flush = True)
			return False
	else:
		print('Spotify error: ' + str(post_response.status_code) + ' ' + res_json['error'], flush=True )
		return False


"""
Requests an access token from the Spotify API with a refresh token. Only called if an access
token and refresh token were previously acquired.
Returns: either [access token, expiration time] or None if request failed
"""
def refreshToken(session):

	if time.time() > (session['token_expiration'] - 60):

		headers = {'Authorization': 'Basic ' + createAuthorization(), 'Accept': 'application/json', 'Content-Type': 'application/x-www-form-urlencoded'}
		body = {'refresh_token': session['refresh_token'], 'grant_type': 'refresh_token'}
		post_response = requests.post(TOKEN_BASE, headers=headers, data=body)

		# 200 code indicates access token was properly granted
		if post_response.status_code == 200:
			res_json = post_response.json()
			session['access_token'] = res_json['access_token']
			session['token_expiration'] = time.time() + res_json['expires_in']
			return True
		else:
			print('Error acquiring refreshed token' + str(post_response.status_code), flush = True)
			return False
	else:
		return True

'''
GET REQUESTS: PLAYLISTS
Functions to perfrom GET requests to acquire User playlists. These are then supplied to the user in a <select> menu to choose the playlist
to randomize. 
Functions to perform GET requests to acquire the items in the selected playlist.
'''

'''
Make single request to playlist api to get list of playlists (max 50 playlists). Add to supplied list of playlists.
Return: Updated list of playlists and the total number of playlists in the user account.
'''

def getUserPlaylist(playlists, token, user_id, offset = 0):

	playlistURL = f'https://api.spotify.com/v1/users/{user_id}/playlists'
	headers = {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'}
	params = {'limit':'50', 'offset' :str(offset)}

	response = requests.get(playlistURL, headers=headers, params=params)
	if not response:
		print('No playlist response', flush = True) 
		return None, None

	# 200 code indicates playlists properly returned
	if response.status_code == 200 :
		for playlist in response.json()['items']:
			playlists.append((playlist['name'], playlist['uri'])) if playlist['owner'] ['display_name'] == user_id else None
			total = response.json()['total']
	else:
		print('Error getting playlists' +  str(response.status_code), flush = True)
		return None, None
	return playlists, response.json()['total']

'''
Refresh token and make series of api calls to acquire all user playlists.
Return: List of all user playlists in the form (playlist name, playlist id)
'''

def getAllPlaylists(session):
	refreshStatus = refreshToken(session)
	if not refreshStatus:
		return None
	
	playlists, total = getUserPlaylist([], session['access_token'], session['user_id']) 
	if not playlists: return None


	#Continue making API calls if there are more than 50 playlists (max returned in 1 api call)
	offset = 50 
	while total>offset:
		playlistsTemp, totalTemp = getUserPlaylist(playlists, session['access_token'], session['user_id'], offset=offset)
		playlists, total = playlistsTemp, totalTemp if playlistsTemp and totalTemp else playlists, total
		offset += 50
	
	return sorted(playlists, key=lambda tup:tup[0].lower())

'''
Make single request to playlist api to get tracks in given playlist (max 50 tracks). Add to supplied list of tracks
Return: Updated list of tracks and the total number of tracks in the user account.
'''

def getPlaylistItems(playlist, token, playlist_id, offset = 0):
	itemsURL = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
	headers = {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'}
	params = {'limit':'50', 'offset' :str(offset), 'fields' : 'total, items(track(name, uri))'}

	response = requests.get(itemsURL, headers=headers, params=params)
	if not response:
		print('No items response', flush = True) 
		return None, None

	# 200 code indicates items properly returned	
	if response.status_code == 200 :
		for item in response.json()['items']:
			playlist.append((item['track']['name'], item['track']['uri']))
			total = response.json()['total']
	else:
		print('Error getting playlist items' +  str(response.status_code), flush = True)
		return None, None
	return playlist, response.json()['total']

'''
Refresh token and make series of api calls to acquire all tracks in a given playlist.
Return: List of all tracks in the playlist in the form (track name, track id)
'''

def getAllPlaylistItems(session, playlist_id):
	refreshStatus = refreshToken(session)
	if not refreshStatus:
		return None
	
	#extract just the id from API returned value 'spotify:playlist:id'
	playlist_id = playlist_id.split(':')[2]
	
	playlist, total = getPlaylistItems([], session['access_token'] , playlist_id) 
	if not playlist: return None

	#Continue making API calls if there are more than 50 items in the playlist (max returned in 1 api call)
	offset = 50 
	while total>offset:
		playlistTemp, totalTemp = getPlaylistItems(playlist, session['access_token'], playlist_id, offset=offset)
		playlist, total = (playlistTemp, totalTemp) if (playlistTemp and totalTemp) else (playlist, total)
		offset += 50
	return playlist

def addReplacePlaylist(token, playlist_id, uris, replace=False):
	playlistURL = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
	headers = {'Authorization': 'Bearer ' + token, 'Accept': 'application/json', 'Content-Type': 'application/json'}
	body = json.dumps({'uris':uris})

	response = requests.put(playlistURL, headers=headers, data=body) if replace else requests.post(playlistURL, headers=headers, data=body)
	if response.status_code == 201:
		return True
	print(response.status_code, flush=True)
	return False

def updatePlaylistItems(session, playlist_id, tracks):
	refreshStatus = refreshToken(session)
	if not refreshStatus:
		return False
	
	playlist_id = playlist_id.split(':')[2]

	index = 0
	while(index < len(tracks)):
		uriList = [track[1] for track in tracks if tracks.index(track) in range(index, index + 100)]
		uriString = ','.join(uriList)
		status = addReplacePlaylist(session['access_token'], playlist_id, uriList, replace = (index==0))
		if not status: return False
		index += 100
	return True
