import json
import urllib.parse

import requests
from django.http import HttpResponseNotFound
from rest_framework.response import Response
from requests import ConnectionError

from authors.models.author import Author
from authors.serializers.author_serializer import AuthorSerializer


class NodeConfigBase:
    """
    Serves as sample and base configuration for remote server/node specific implementations

    Remember to call super whenever possible; use good judgment to determine when to call super in the method body.
    """

    """
    Call domain with self.__class__.domain so you can override it in classes that inherit this.
    Inheriting classes may not need it unless when needed
    """
    domain = 'domain.herokuapp.com'
    username = 'domain'
    author_serializer = AuthorSerializer
    """Mapping: remote to local"""
    remote_fields = {
        'id': 'official_id',
        'url': 'url',
        'host': 'host',
        'displayName': 'display_name',
        'github': 'github',
        'profileImage': 'profile_image'
    }

    def __init__(self):
        try:
            self.node_author = Author.objects.get(username=self.__class__.username)
            self.node_detail = self.node_author.node_detail
            self.username = self.node_detail.remote_username
            self.password = self.node_detail.remote_password
        except Exception as e:
            print(f'Author does not exist yet...: {e}')

    @classmethod
    def create_dictionary_entry(cls):
        return {cls.domain: cls()}

    def get_base_url(self):
        return f'http://{self.__class__.domain}'

    def get_all_author_jsons(self, params: dict):
        """Returns a list of authors as json"""
        url = f'{self.get_base_url()}/authors/'
        if len(params) > 0:
            query_param = urllib.parse.urlencode(params)
            url += '?' + query_param

        try:
            response = requests.get(url, auth=(self.username, self.password))
        except ConnectionError:
            return None
        except Exception as e:
            print(f"NodeConfigBase: Unknown err: {e}")
            return None

        if response.status_code == 200:
            author_jsons = json.loads(response.content.decode('utf-8'))
            return author_jsons['items']
        return None

    # endpoints
    def get_all_authors_request(self, params: dict):
        """Returns all authors as a valid HTTP Response"""
        author_jsons = self.get_all_author_jsons(params)

        if author_jsons is None:
            return HttpResponseNotFound()
        return Response({
            "type": "authors",
            "items": author_jsons
        })

    def from_author_id_to_url(self, author_id: str) -> str:
        url = f'{self.get_base_url()}/authors/{author_id}/'
        response = requests.get(url, auth=(self.username, self.password))
        if response.status_code == 200:
            # todo(turnip): map to our author?
            json_dict = json.loads(response.content)
            return json_dict['url']
        return None

    def from_author_id_to_author(self, author_id: str) -> Author:
        url = f'{self.get_base_url()}/authors/{author_id}/'
        return self.get_author_via_url(url)

    def get_author_request(self, author_id: str):
        response = requests.get(f'{self.get_base_url()}/authors/{author_id}/', auth=(self.username, self.password))
        if response.status_code == 200:
            # todo(turnip): map to our author?
            return Response(json.loads(response.content))
        return HttpResponseNotFound()

    def get_author_via_url(self, author_url: str) -> Author:
        response = requests.get(author_url, auth=(self.username, self.password))

        if response.status_code == 200:
            author_json = json.loads(response.content.decode('utf-8'))
            serializer = AuthorSerializer(data=author_json)

            if serializer.is_valid():
                return serializer.validated_data  # <- GOOD RESULT HERE!!!

            print('GetAuthorViaUrl: AuthorSerializer: ', serializer.errors)

        return None

    def get_all_followers_request(self, params: dict, author_id: str):
        url = f'{self.get_base_url()}/authors/{author_id}/followers/'
        if len(params) > 0:
            query_param = urllib.parse.urlencode(params)
            url += '?' + query_param
        response = requests.get(url, auth=(self.username, self.password))
        if response.status_code == 200:
            # todo(turnip): map to our author?
            return Response(json.loads(response.content))
        return HttpResponseNotFound()

    def post_local_follow_remote(self, actor_url: str, target_id: str) -> dict:
        """Make call to remote node to follow"""
        target_author_url = self.from_author_id_to_url(target_id)
        if target_author_url is None:
            return 404
        url = f'{target_author_url}/followers/'
        response = requests.post(url,
                                 auth=(self.username, self.password),
                                 data={'actor': actor_url})
        if 200 <= response.status_code < 300:
            try:
                return json.loads(response.content.decode('utf-8'))
            except Exception as e:
                print(f"Failed to deserialize response: {response.content}")
        else:
            print(f"post_local_follow_remote: remote server response: {response.status_code}")
        return response.status_code

    ## will have to change the url depending on what team it is 
    # dictionary: [host + endpoint, formatted url]
    # will have to change the data for team 10
    def send_to_remote_inbox(self, data, target_author_url):
        if target_author_url is None:
            return 404
        url = f'{target_author_url}/inbox'
        return requests.post(url = url, data = json.dumps(data), auth = (self.username, self.password), headers = {'content-type': 'application/json'})

    def get_authors_liked_on_post(self, object_id):
        url = f'{self.get_base_url()}{object_id}'
        return requests.get(url = url, auth = (self.username, self.password))

    def get_authors_liked_on_comment(self, object_id):
        url = f'{self.get_base_url()}{object_id}'
        return requests.get(url = url, auth = (self.username, self.password))

    def get_authors_likes(self, target_author_url):
        url = f'{target_author_url}/liked'
        return requests.get(url = url, auth = (self.username, self.password))

    def get_post_by_post_id(self, post_url):
        url = f'{self.get_base_url()}{post_url}'
        return requests.get(url = url, auth = (self.username, self.password))

    def get_authors_posts(self, author_posts_path):
        url = f'{self.get_base_url()}{author_posts_path}'
        return requests.get(url = url, auth = (self.username, self.password))

    def get_comments_for_post(self, comments_path):
        url = f'{self.get_base_url()}{comments_path}'
        return requests.get(url = url, auth = (self.username, self.password))
