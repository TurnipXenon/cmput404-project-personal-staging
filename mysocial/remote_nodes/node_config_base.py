import json
import urllib.parse

import requests
from django.http import HttpResponseNotFound
from django.utils.baseconv import base64
from rest_framework.response import Response

from authors.models.author import Author
from authors.serializers.author_serializer import AuthorSerializer
from mysocial.settings import base


class NodeConfigBase:
    """
    Sample and base config

    Remember to call super whenever possible; use good judgment to determine when to call super in the method body.
    """

    """
    Call domain with self.__class__.domain so you can override it in classes that inherit this.
    Inheriting classes may not need it unless when needed
    """
    domain = 'domain.herokuapp.com'
    author_serializer = AuthorSerializer

    def __init__(self):
        if base.CURRENT_DOMAIN not in base.REMOTE_CONFIG_CREDENTIALS:
            print(f'{self.__class__.domain} is not in ConfigVars REMOTE_CONFIG_CREDENTIALS')
            self.username = 'username'
            self.password = 'password'
            return

        credentials = base.REMOTE_CONFIG_CREDENTIALS[base.CURRENT_DOMAIN]
        print(credentials)
        self.username = credentials['username']
        self.password = credentials['password']
        # todo(turnip): check entry in Author, check if inactive?

    @classmethod
    def create_dictionary_entry(cls):
        return {cls.domain: cls()}

    # endpoints
    def get_all_authors_request(self, params: dict):
        url = f'http://{self.__class__.domain}/authors/'
        if len(params) > 0:
            query_param = urllib.parse.urlencode(params)
            url += '?' + query_param
        response = requests.get(url)
        if response.status_code == 200:
            # todo(turnip): map to our author?
            return Response(json.loads(response.content))
        return HttpResponseNotFound()

    def from_author_id_to_url(self, author_id: str):
        response = requests.get(f'http://{self.__class__.domain}/authors/{author_id}/')
        if response.status_code == 200:
            # todo(turnip): map to our author?
            json_dict = json.loads(response.content)
            return json_dict['url']
        return None

    def get_author_request(self, author_id: str):
        response = requests.get(f'http://{self.__class__.domain}/authors/{author_id}/')
        if response.status_code == 200:
            # todo(turnip): map to our author?
            return Response(json.loads(response.content))
        return HttpResponseNotFound()

    def get_author_via_url(self, author_url: str) -> dict:
        # token = base64.b64encode(f'{self.username}:{self.password}'.encode('ascii')).decode('utf-8')
        # headers = {'HTTP_AUTHORIZATION': f'Basic {token}'}
        response = requests.get(author_url, auth=(self.username, self.password))

        if response.status_code == 200:
            # todo(turnip): map to our author?
            return json.loads(response.content.decode('utf-8'))
        else:
            return None

    def get_all_followers_request(self, params: dict, author_id: str):
        url = f'http://{self.__class__.domain}/authors/{author_id}/followers/'
        if len(params) > 0:
            query_param = urllib.parse.urlencode(params)
            url += '?' + query_param
        response = requests.get(url)
        if response.status_code == 200:
            # todo(turnip): map to our author?
            return Response(json.loads(response.content))
        return HttpResponseNotFound()

    def post_local_follow_remote(self, actor_url: str, target_id: str):
        """Make call to remote node to follow"""
        target_author_url = self.from_author_id_to_url(target_id)
        url = f'{target_author_url}/followers/'
        # todo: change with our own credential!!!!
        response = requests.post(url,
                                 auth=(self.username, self.password),
                                 data={'actor': actor_url})
        if 200 <= response.status_code < 300:
            return Response(json.loads(response.content))
        # todo: fix non-RESTful response; some cases need to return 500
        return Response(status=response.status_code)
