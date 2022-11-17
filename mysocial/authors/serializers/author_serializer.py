import pathlib
from urllib.parse import urlparse

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
        if model.host == '':
            return base.CURRENT_DOMAIN

        return model.host

    def to_internal_value(self, data: dict) -> Author:
        """
        Does not work with remote Author
        :param data:
        :return: Access serializers.validated_data for deserialized version of the json converted to Author
        """

        for required_field in AuthorSerializer.Meta.required_fields:
            if required_field not in data:
                raise serializers.ValidationError(f'AuthorSerializer: missing field: {required_field}')

        url = data['url']
        # by Philipp Claßen from https://stackoverflow.com/a/56476496/17836168
        _, host, path, _, _, _ = urlparse(url)

        try:
            if host == base.CURRENT_DOMAIN:
                local_id = pathlib.PurePath(path).name
                # deserialize a local author
                author = Author.objects.get(official_id=local_id)
            else:
                # deserialize a remote author; take not it's missing some stuff so check with is_local()
                author = Author()
                node_config = base.REMOTE_CONFIG.get(host)
                if node_config is None:
                    print(f"AuthorSerializer: Host not found: {host}")
                    return serializers.ValidationError(f"AuthorSerializer: Host not found: {host}")
                remote_fields: dict = node_config.remote_fields

                for remote_field, local_field in remote_fields.items():
                    if remote_field not in data:
                        continue
                    elif remote_field == 'url':
                        # special case
                        sanitized: str = data[remote_field]
                        for start in ('http://', 'https://'):
                            if sanitized.startswith(start):
                                sanitized = sanitized[len(start):]
                        setattr(author, local_field, f'https://{sanitized}')
                    else:
                        setattr(author, local_field, data[remote_field])
                author.host = host  # force a set even if field was not given
        except Exception as e:
            print(f"AuthorSerializer: failed serializing {e}")
            raise serializers.ValidationError(f"AuthorSerializer: failed serializing {e}")

        return author

    class Meta:
        model = Author
        fields = ('type', 'id', 'url', 'host', 'displayName', 'github', 'profileImage')

        # custom fields
        required_fields = ('url',)
