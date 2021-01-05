#MODULES
#For non-standard or missing module x, try [pip install x] from the command line.
import requests
import base64
import datetime
import time
from urllib.parse import urlencode

#CLIENT INFO
#This relates to the app, and not to the user.
#Ideally, these would be environmental variables declared elsewhere i.e. not visible to the user.
#Register at [developer.spotify.com/dashboard/login] to obtain your own client_id and client_secret.
client_id = ""
client_secret = ""

class Spotify(object):
	access_token = None
	access_token_expires = datetime.datetime.now()
	access_token_did_expire = True

	def __init__(self, client_id, client_secret, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.client_id = client_id
		self.client_secret = client_secret

	#AUTHORISATION FUNCTIONS
	def get_authorization_header(self):
		if self.client_secret == None or self.client_id == None:
			raise Exception("Missing client_id and/or client_secret.")

		#Constructs a b64 byte-string, "client_id:client_secret".
		client_credentials = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode('utf-8'))

		return {"Authorization": f"Basic {client_credentials.decode()}"}

	def perform_authorization(self):
		#Requests authorization from Spotify, and updates class variables if successful.
		r = requests.post("https://accounts.spotify.com/api/token", 
			data={"grant_type":"client_credentials"}, 
			headers=self.get_authorization_header()
			)

		if r.status_code not in range(200,299):
			raise Exception(f"Could not authenticate client, received error code:{r.status_code}")

		#Update client-class variables 
		self.access_token = r.json()['access_token']
		self.access_token_expires = datetime.datetime.now() + datetime.timedelta(seconds=r.json()['expires_in'])
		self.access_token_did_expire = (datetime.datetime.now() + datetime.timedelta(seconds=r.json()['expires_in'])) < datetime.datetime.now()

		return True

	def get_access_token(self):
		#Returns access-token, and if expired, gets a new one.
		if self.access_token_expires < datetime.datetime.now():
			self.perform_authorization()
			return self.get_access_token()
		elif self.access_token == None:
			self.perform_authorization()
			return self.get_access_token()

		return self.access_token

	#SEARCH FUNCTIONS
	def get_resource_header(self):
		#Embeds an access-token into a generic resource request header.
		access_token = self.get_access_token()
		headers = {"Authorization": f"Bearer {access_token}"}
		return headers

	def base_search(self, query_params):
		#Combines a generic header and generic endpoint with generic query parameters.
		#Returns a json object.
		headers = self.get_resource_header()
		endpoint = "https://api.spotify.com/v1/search"
		lookup_url = f"{endpoint}?{query_params}"
		r = requests.get(lookup_url, headers=headers)
		if r.status_code not in range (200,299):
			return {}
		return r.json()

	def search(self, query=None, operator=None, operator_query=None, search_type='artist'):
	#A more robust search function which constructs a detailed set of query parameters.
	#Accepts a dictionary of query parameters
		if query == None:
			raise Exception("ERROR: search did not receive a query.")
		if isinstance(query, dict):
			query == " ".join([f"{k}:{v}" for k,v in query.items()])
		if operator != None and operator_query != None:
			if operator.lower() == "or" or operator.lower() == "not":
				operator = operator.upper()
				if isinstance(operator_query, str):
					query = f"{query} {operator} {operator_query}"
		query_params = urlencode({"q": query, "type": search_type.lower()})

		return self.base_search(query_params)

	#RESOURCE SPECIFIC FUNCTIONS
	def show(get_function):
		#A decorator to show results more clearly.
		def wrapper(*args, **kwargs):
			r = get_function(*args,**kwargs)
			for k,v in r.items():
				print(k.upper(), ':', v, "\n")		
		return wrapper

	def get_resource(self, lookup_id, resource_type, extension="",version="v1"):
		#Template for most basic resource requests.
		endpoint = f"https://api.spotify.com/{version}/{resource_type}/{lookup_id}/{extension}"
		headers = self.get_resource_header()
		r = requests.get(endpoint, headers=headers)
		if r.status_code not in range(200,299):
			return {}
		return r.json()

	def get_resources(self, lookup_ids, resource_type, version="v1"):
		#Expects a list or tup of lookup_ids
		ids_string = ",".join(lookup_ids)  
		endpoint = f"https://api.spotify.com/{version}/{resource_type}?ids={ids_string}"
		headers = self.get_resource_header()
		r = requests.get(endpoint, headers=headers)
		if r.status_code not in range(200,299):
			return {}
		return r.json()

	def get_album(self, lookup_id):
		return self.get_resource(lookup_id, resource_type="albums")

	def get_album_tracks(self, lookup_id):
		return self.get_resource(lookup_id, resource_type="albums", extension="tracks")

	def get_albums(self, lookup_ids):
		return self.get_resources(lookup_ids, resource_type="albums", version="v1")
		
	def get_artist(self, lookup_id):
		return self.get_resource(lookup_id, resource_type="artists")

	def get_artist_albums(self, lookup_id):
		return self.get_resource(lookup_id, resource_type="artists", extension="albums")

	def get_artist_top_tracks(self, lookup_id):
		return self.get_resource(lookup_id, resource_type="artists", extension="top-tracks?country=GB")

	def get_artist_related_artists(self, lookup_id):
		return self.get_resource(lookup_id, resource_type="artists", extension="related-artists")

	def get_artists(self, lookup_ids):
		return self.get_resources(lookup_ids, resource_type="artists", version="v1")

	def get_track(self, lookup_id):
		return self.get_resource(lookup_id, resource_type="tracks")

	def get_tracks(self, lookup_ids):
		return self.get_resources(lookup_ids, resource_type="tracks")

	def get_audio_analysis(self, lookup_id):
		return self.get_resource(lookup_id, resource_type="audio-analysis")

	def get_audio_features(self, lookup_id):
		return self.get_resource(lookup_id, resource_type="audio-features")

	def get_audio_features_for_several_tracks(self, lookup_ids):
		return self.get_resources(lookup_ids, resource_type="audio-features")

	def get_album_tracks_ids(self, album_id):
		#returns a list containing the ids for each track of an album
		r = self.get_album_tracks(album_id)
		album_tracks_ids = []
		for i in r['items']:
			 album_tracks_ids.append(i['id'])
		return album_tracks_ids










