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

	def show(get_function):
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

	def get_album(self, lookup_id):
		return self.get_resource(lookup_id, resource_type="albums")

	def get_album_tracks(self, lookup_id):
		return self.get_resource(lookup_id, resource_type="albums", extension="tracks")
		
	def get_artist(self, lookup_id):
		return self.get_resource(lookup_id, resource_type="artists")

	def get_artist_albums(self, lookup_id):
		return self.get_resource(lookup_id, resource_type="artists", extension="albums")

	def get_artist_top_tracks(self, lookup_id):
		return self.get_resource(lookup_id, resource_type="artists", extension="top-tracks?country=GB")

	def get_artist_related_artists(self, lookup_id):
		return self.get_resource(lookup_id, resource_type="artists", extension="related-artists")

	def get_artists(self, lookup_ids, resource_type="artists", version="v1"):
		#Expects a list or tup of artist ids.
		ids_string = ",".join(lookup_ids)  
		endpoint = f"https://api.spotify.com/{version}/{resource_type}?ids={ids_string}"
		headers = self.get_resource_header()
		r = requests.get(endpoint, headers=headers)
		if r.status_code not in range(200,299):
			return {}
		return r.json()



