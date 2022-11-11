import pathlib
import uuid
from urllib.parse import urlparse

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models

from mysocial.settings import base
from remote_nodes.remote_util import RemoteUtil
from .author_manager import AuthorManager


class AuthorType(models.TextChoices):
    LOCAL_AUTHOR = "local_author"
    ACTIVE_REMOTE_NODE = "active_remote_node"
    INACTIVE_REMOTE_NODE = "inactive_remote_node"  # we can deactivate nodes by just changing their type


class Author(AbstractUser):
    """
    Fields:
    - Inherited fields not shown below:
        :ivar id: auto generated BigInt
        :ivar password: str; encrypted
        :ivar last_login: datetime
        :ivar is_superuser: bool
        :ivar username: str; unique constraint
        :ivar email: str; unique constraint
        :ivar is_staff: bool
        :ivar is_active: bool
        :ivar date_joined: datetime

    from: https://simpleisbetterthancomplex.com/tutorial/2016/07/22/how-to-extend-django-user-model.html
    """
    URL_PATH = "authors"

    # Remove this unnecessary fields
    first_name = None
    last_name = None

    official_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    host = models.TextField(blank=True)
    display_name = models.TextField(blank=True)
    github = models.TextField(blank=True)
    profile_image = models.ImageField(blank=True)
    author_type = models.CharField(choices=AuthorType.choices, default=AuthorType.LOCAL_AUTHOR, max_length=25)

    objects = AuthorManager()

    REQUIRED_FIELDS = ['email', 'password']

    def get_url(self):
        """
        Returns author_url following the local_author's format
        Example:
            - http://socioecon/authors/{self.official_id}
            - http://{local_host}/authors/{self.official_id}
        """
        return self.get_id()

    def get_id(self):
        """
        Returns author_url following the local_author's format
        Example:
            - http://socioecon/authors/{self.official_id}
            - http://{local_host}/authors/{self.official_id}
        """
        return f"http://{base.CURRENT_DOMAIN}/{Author.URL_PATH}/{self.official_id}"

    @staticmethod
    def get_serializer_field_name():
        return "author"

    def __str__(self):
        return self.display_name if self.display_name else self.username

    @property
    def is_authenticated(self):
        """
        :return: True if the current user is an authenticated local_author or active_remote_node.
        """
        return self.author_type != AuthorType.INACTIVE_REMOTE_NODE and super().is_authenticated

    @property
    def is_authenticated_user(self):
        """
        :return: True if the current user is an authenticated or logged in local_author.
        """
        return self.author_type == AuthorType.LOCAL_AUTHOR and super().is_authenticated

    @property
    def is_authenticated_node(self):
        """
        :return: True if the current user is an authenticated active_remote_node.
        """
        return self.author_type == AuthorType.ACTIVE_REMOTE_NODE and super(Author, self).is_authenticated

    @staticmethod
    def get_author(official_id: str):
        """
        Gets a local author ONLY. Nodes are ignored.
        :param official_id:
        :return: A local_author
        """
        try:
            return Author.objects.get(
                official_id=official_id,
                author_type=AuthorType.LOCAL_AUTHOR
            )
        except Author.DoesNotExist:
            return None

    @staticmethod
    def get_all_authors():
        """
        Gets all local_author. Nodes are ignored.
        :return: All local_authors.
        """
        return Author.objects.filter(author_type=AuthorType.LOCAL_AUTHOR)


# These functions are outside Author to prevent circular dependency and IDEs struggling figuring out type hinting
def from_author_url_to_author(author_url: str) -> (Author, ValidationError):
    """
    Convert url to Author

    :param author_url:
    :return: Returns a pair of Author and ValidationError

    Example:
        author, err = from_url_to_author(url)

        if err is not None:
            # handle error
            return

        # do logic with author
    """
    # by Philipp Claßen from https://stackoverflow.com/a/56476496/17836168
    _, domain, path, _, _, _ = urlparse(author_url)

    if domain == base.CURRENT_DOMAIN:
        local_id = from_author_url_to_local_id(path)
        author = Author.get_author(official_id=local_id)
        err = None
        if author is None:
            err = ValidationError(f'There is no local_author with id {path.name}')
        return author, err

    # check if we have this server
    if domain not in RemoteUtil.CONFIG:
        return None, ValidationError(f'{author_url} does not have any corresponding domain')

    # todo: otherwise, check it at the other server; implement
    node_config = RemoteUtil.CONFIG[domain]
    author = node_config.get_author(author_url)
    if author is None:
        return None, ValidationError(f'{author_url} does not exist in the domain {domain}')
    return author, None


def validate_author_url(author_url: str):
    """
    Do validations only; for Model fields
    :param author_url:
    :return:
    """
    _, err = from_author_url_to_author(author_url)
    if err:
        raise err


def from_author_url_to_local_id(local_author_url: str):
    """
    Note: this does NOT validate if the url is not from a local author
    :return:
    """
    return pathlib.PurePath(local_author_url).name
