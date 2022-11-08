import logging

from django.db import IntegrityError
from django.http.response import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound, HttpResponseForbidden
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from authors.models.author import Author
from authors.serializers.author_serializer import AuthorSerializer
from common.pagination_helper import PaginationHelper
from follow.follow_util import FollowUtil
from follow.models import Follow
from follow.serializers.follow_serializer import FollowRequestListSerializer, FollowRequestSerializer
from rest_framework import serializers

logger = logging.getLogger(__name__)


# todo(turnip): Refactor when tests are available

class OutgoingRequestView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FollowRequestListSerializer

    def get_queryset(self):
        return None

    @staticmethod
    @extend_schema(
        parameters=PaginationHelper.OPEN_API_PARAMETERS,
        summary="outgoing_follow_requests_all"
    )
    def get(request: Request) -> HttpResponse:
        """Get all outgoing follow requests that were not accepted yet"""
        relationships = Follow.objects.filter(actor=request.user, has_accepted=False)
        serializers = FollowRequestSerializer(relationships, many=True)
        data, err = PaginationHelper.paginate_serialized_data(request, serializers.data)
        if err is not None:
            return HttpResponseNotFound()
        return Response(data={
            'type': 'followRequests',
            'items': data,
        })


class IncomingRequestView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FollowRequestListSerializer

    def get_queryset(self):
        return None

    @staticmethod
    @extend_schema(
        parameters=PaginationHelper.OPEN_API_PARAMETERS,
        summary="incoming_follow_requests_all"
    )
    def get(request: Request) -> HttpResponse:
        """
        Get all incoming follow requests

        User story: as an author: I want to un-befriend local and remote authors.
        todo(turnip): remote authors not yet implemented

        User story: as an author: I want to know if I have friend requests.
        todo(turnip): remote authors not yet implemented

        User story: as an author, When I befriend someone (they accept my friend request) I follow them, only when the
        other author befriends me do I count as a real friend – a bi-directional follow is a true friend.
        todo(turnip): remote authors not yet implemented

        User story: As an author, I want to befriend local authors

        See the step-by-step calls to follow or befriend someone at:
        https://github.com/hgshah/cmput404-project/blob/main/endpoints.txt#L137
        """
        relationships = Follow.objects.filter(target=request.user, has_accepted=False)
        serializers = FollowRequestSerializer(relationships, many=True)
        data, err = PaginationHelper.paginate_serialized_data(request, serializers.data)
        if err is not None:
            return HttpResponseNotFound()
        return Response(data={
            'type': 'followRequests',
            'items': data,
        })


class IndividualRequestView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FollowRequestSerializer

    def get_queryset(self):
        return None

    @staticmethod
    def get(request: Request, follow_id: str = None) -> HttpResponse:
        """
        Get an individual follow request

        User story: as an author: I want to un-befriend local and remote authors.
        todo(turnip): remote authors not yet implemented

        User story: as an author, When I befriend someone (they accept my friend request) I follow them, only when the
        other author befriends me do I count as a real friend – a bi-directional follow is a true friend.
        todo(turnip): remote authors not yet implemented

        User story: As an author, I want to befriend local authors

        See the step-by-step calls to follow or befriend someone at:
        https://github.com/hgshah/cmput404-project/blob/main/endpoints.txt#L137
        """
        try:
            follow = Follow.objects.get(id=follow_id)
            if follow.target != request.user and follow.actor != request.user:
                # Only the two accounts should be able to delete an account
                # Returning not found due to security concerns
                return HttpResponseNotFound()
            serializers = FollowRequestSerializer(follow)
            return Response(data=serializers.data)
        except Follow.DoesNotExist:
            return HttpResponseNotFound()
        except Exception as e:
            logger.error(f'IncomingRequestPutView: put: unknown error: {e}')
            return HttpResponseBadRequest()

    @staticmethod
    def put(request: Request, follow_id: str = None) -> HttpResponse:
        """
        Accept a follow request
        Only the target or object can accept the actor's request.
        This is only one way. You cannot make a follow back into has_accepted = False, you have to delete it.

        User story: as an author: I want to un-befriend local and remote authors.
        todo(turnip): remote authors not yet implemented

        User story: as an author, When I befriend someone (they accept my friend request) I follow them, only when the
        other author befriends me do I count as a real friend – a bi-directional follow is a true friend.
        todo(turnip): remote authors not yet implemented

        See the step-by-step calls to follow or befriend someone at:
        https://github.com/hgshah/cmput404-project/blob/main/endpoints.txt#L137
        """
        try:
            follow = Follow.objects.get(id=follow_id)
            if follow.target != request.user:
                # Only the two accounts should be able to delete an account
                # Returning not found due to security concerns
                return HttpResponseNotFound()
            if Follow.FIELD_NAME_HAS_ACCEPTED not in request.data \
                    or not request.data[Follow.FIELD_NAME_HAS_ACCEPTED]:
                # You cannot make a follow back into has_accepted = False, you have to delete it.
                return HttpResponseBadRequest()

            follow.has_accepted = True
            follow.save()
            serializers = FollowRequestSerializer(follow)
            return Response(data=serializers.data)
        except Follow.DoesNotExist:
            return HttpResponseNotFound()
        except Exception as e:
            logger.error(f'IncomingRequestPutView: put: unknown error: {e}')
            return HttpResponseBadRequest()

    @staticmethod
    def delete(request: Request, follow_id: str = None) -> HttpResponse:
        """
        Delete, decline, or cancel a follow request

        User story: as an author: I want to un-befriend local and remote authors.
        todo(turnip): remote authors not yet implemented
        """
        if not request.user.is_authenticated:
            return HttpResponseNotFound()

        try:
            follow = Follow.objects.get(id=follow_id)
            if follow.target != request.user and follow.actor != request.user:
                # Only the two accounts should be able to delete an account
                # Returning not found due to security concerns
                return HttpResponseNotFound()

            follow.delete()
            return Response(status=204)
        except Follow.DoesNotExist:
            return HttpResponseNotFound()
        except Exception as e:
            logger.error(f'IncomingRequestPutView: put: unknown error: {e}')
            return HttpResponseBadRequest()


class FollowersView(GenericAPIView):
    def get_queryset(self):
        return None

    def get_serializer_class(self):
        return FollowRequestSerializer

    @staticmethod
    @extend_schema(parameters=PaginationHelper.OPEN_API_PARAMETERS)
    def get(request: Request, author_id: str = None) -> HttpResponse:
        """
        Get followers for an Author

        See the step-by-step calls to follow or befriend someone at:
        https://github.com/hgshah/cmput404-project/blob/main/endpoints.txt#L137

        User story: As an author, my server will know about my friends
        """
        user = None
        try:
            user = Author.objects.get(official_id=author_id)
        except Author.DoesNotExist:
            return HttpResponseNotFound()
        # reference: https://stackoverflow.com/a/9727050/17836168
        followers = FollowUtil.get_followers(user)
        serializers = AuthorSerializer(followers, many=True)
        data, err = PaginationHelper.paginate_serialized_data(request, serializers.data)
        if err is not None:
            return HttpResponseNotFound()
        return Response(data={
            'type': 'followers',
            'items': data,
        })

    @staticmethod
    def post_local_author(request: Request, author_id: str = None) -> HttpResponse:
        actor = request.user
        target = None
        data = None
        try:
            target = Author.objects.get(official_id=author_id)
            if target == actor:
                # validation: do not follow self!
                return HttpResponseBadRequest('You can not follow self')

            follow = Follow.objects.create(actor=actor, target=target, has_accepted=False)
            serializers = FollowRequestSerializer(follow)
            data = serializers.data
        except Author.DoesNotExist:
            return HttpResponseNotFound()
        except IntegrityError:
            return HttpResponseBadRequest('You\'re either following this account or have already made a follow request')
        except Exception as e:
            logger.error(f'FollowersView: post: unknown error: {e}')
            return HttpResponseBadRequest()
        return Response(data=data, status=201)

    @staticmethod
    def post_remote_node(request: Request, author_id: str = None) -> HttpResponse:
        # we want to get the author representation of the
        return Response(status=201)

    @staticmethod
    def post(request: Request, author_id: str = None) -> HttpResponse:
        """
        Create a follow request for the local author

        Two cases:
        (1) A local author makes a follow request to a local author
        (2) A remote node tells us that one of its users wants to follow us todo(turnip)

        User story: as an author: I want to un-befriend local and remote authors.
        todo(turnip): remote authors not yet implemented

        User story: as an author, When I befriend someone (they accept my friend request) I follow them, only when the
        other author befriends me do I count as a real friend – a bi-directional follow is a true friend.
        todo(turnip): remote authors not yet implemented

        See the step-by-step calls to follow or befriend someone at:
        https://github.com/hgshah/cmput404-project/blob/main/endpoints.txt#L137
        """
        if not request.user.is_authenticated:
            return HttpResponseNotFound()

        if request.user.is_authenticated_user:
            return FollowersView.post_local_author(request, author_id=author_id)

        if request.user.is_authenticated_node:
            return FollowersView.post_local_author(request, author_id=author_id)

        return HttpResponseForbidden()


# todo(turnip): add test
class RealFriendsView(GenericAPIView):
    def get_queryset(self):
        return None

    def get_serializer_class(self):
        return FollowRequestSerializer

    @staticmethod
    @extend_schema(
        parameters=PaginationHelper.OPEN_API_PARAMETERS,
        responses=inline_serializer(
            name='RealFriends',
            fields={
                'type': serializers.CharField(),
                'items': AuthorSerializer(many=True)
            }
        )
    )
    def get(request: Request, author_id: str = None) -> HttpResponse:
        """
        Get friends, real friends, true friends, or mutual followers for an Author

        User story: as an author, When I befriend someone (they accept my friend request) I follow them, only when the
        other author befriends me do I count as a real friend – a bi-directional follow is a true friend.
        todo(turnip): remote authors not yet implemented

        User story: As an author, posts I create can be a private to my friends.

        User story: As an author, my server will know about my friends
        """
        user = None
        try:
            user = Author.objects.get(official_id=author_id)
        except Author.DoesNotExist:
            return HttpResponseNotFound()
        friends = FollowUtil.get_real_friends(actor=user)
        serializers = AuthorSerializer(friends, many=True)
        data, err = PaginationHelper.paginate_serialized_data(request, serializers.data)
        if err is not None:
            return HttpResponseNotFound()
        return Response(data={
            'type': 'realFriends',
            'items': data,
        })
