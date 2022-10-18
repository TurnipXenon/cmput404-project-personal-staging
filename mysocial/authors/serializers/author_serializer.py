from rest_framework import serializers
from authors.models import Author


class AuthorSerializer(serializers.ModelSerializer):
    """
    based on https://stackoverflow.com/a/18426235/17836168
    Note: We can generalize this btw to use in every serializer out there!
    """
    type = serializers.SerializerMethodField('get_type')
    displayName = serializers.CharField(source='display_name')
    profileImage = serializers.CharField(source='profile_image')
    url = serializers.SerializerMethodField('get_url')

    def get_type(self, model: Author):
        return model.get_serializer_field_name()

    def get_url(self, model: Author):
        # the path after host may vary, e.g. authors/ vs authors/id
        return f"{model.host}/{Author.URL_PATH}/{model.id}"

    class Meta:
        model = Author
        fields = ('type', 'id', 'url', 'host', 'displayName', 'github', 'profileImage')
