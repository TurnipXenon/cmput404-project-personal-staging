from rest_framework import serializers

from authors.models.author import Author
from mysocial.settings import base


class AuthorSerializer(serializers.ModelSerializer):
    """
    based on https://stackoverflow.com/a/18426235/17836168
    Note: We can generalize this btw to use in every serializer out there!
    """
    type = serializers.SerializerMethodField('get_type')
    id = serializers.SerializerMethodField('get_id')
    displayName = serializers.CharField(source='display_name')
    profileImage = serializers.CharField(source='profile_image')
    url = serializers.SerializerMethodField('get_url')
    host = serializers.SerializerMethodField('get_host')

    @staticmethod
    def get_type(model: Author) -> str:
        return model.get_serializer_field_name()

    @staticmethod
    def get_url(model: Author) -> str:
        # they're the same as id, for now
        return AuthorSerializer.get_id(model)

    @staticmethod
    def get_id(model: Author) -> str:
        # the path after host may vary, e.g. authors/ vs authors/id
        return model.get_url()

    @staticmethod
    def get_host(model: Author) -> str:
        # todo(turnip): if remote node: use host
        return base.CURRENT_DOMAIN

    class Meta:
        model = Author
        fields = ('type', 'id', 'url', 'host', 'displayName', 'github', 'profileImage')
