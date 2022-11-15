import logging

from django.db import IntegrityError
from django.http.response import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseNotFound
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
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
from mysocial.settings import base
from remote_nodes.remote_util import RemoteUtil

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
        relationships = Follow.objects.filter(actor=request.user.get_url(), has_accepted=False)
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
        relationships = Follow.objects.filter(target=request.user.get_url(), has_accepted=False)
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
    @extend_schema(
        tags=['follows', RemoteUtil.REMOTE_WIP_TAG],
    )
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
            follow: Follow = Follow.objects.get(id=follow_id)
            user_url = request.user.get_url()
            if follow.target != user_url and follow.actor != user_url:
                # Only the two accounts should be able to delete an account
                # Returning not found due to security concerns
                return HttpResponseNotFound()

            # if remote_url is present, and we are not authoritative, sync!
            if follow.remote_url != '' and follow.actor == user_url:
                # todo(turnip): get Follow object from remote
                # todo(turnip): update our current Follow object
                pass

            serializers = FollowRequestSerializer(follow)
            return Response(data=serializers.data)
        except Follow.DoesNotExist:
            return HttpResponseNotFound()
        except Exception as e:
            logger.error(f'IncomingRequestPutView: put: unknown error: {e}')
            return HttpResponseBadRequest()

    @staticmethod
    @extend_schema(
        tags=['follows', RemoteUtil.REMOTE_WIP_TAG],
    )
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
        # todo(turnip): implement case where remote node informs us that our Follow request was accepted

        try:
            follow = Follow.objects.get(id=follow_id)
            if follow.target != request.user.get_url():
                # Only the two accounts should be able to delete an account
                # Returning not found due to security concerns
                return HttpResponseNotFound()
            if Follow.FIELD_NAME_HAS_ACCEPTED not in request.data \
                    or not request.data[Follow.FIELD_NAME_HAS_ACCEPTED]:
                # You cannot make a follow back into has_accepted = False, you have to delete it.
                return HttpResponseBadRequest()

            follow.has_accepted = True
            follow.save()

            # todo(turnip): update the Follow reference from the remote server

            serializers = FollowRequestSerializer(follow)
            return Response(data=serializers.data)
        except Follow.DoesNotExist:
            return HttpResponseNotFound()
        except Exception as e:
            logger.error(f'IncomingRequestPutView: put: unknown error: {e}')
            return HttpResponseBadRequest()

    @staticmethod
    @extend_schema(
        tags=['follows', RemoteUtil.REMOTE_WIP_TAG],
    )
    def delete(request: Request, follow_id: str = None) -> HttpResponse:
        """
        Delete, decline, or cancel a follow request

        User story: as an author: I want to un-befriend local and remote authors.
        todo(turnip): remote authors not yet implemented
        """
        if not request.user.is_authenticated:
            return HttpResponseNotFound()

        try:
            follow: Follow = Follow.objects.get(id=follow_id)
            if follow.target != request.user.get_url() and follow.actor != request.user.get_url():
                # Only the two accounts should be able to delete an account
                # Returning not found due to security concerns
                return HttpResponseNotFound()

            follow.delete()

            # todo(turnip): if remote, delete Follow reference or mirror from the remote server

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
    @extend_schema(
        parameters=RemoteUtil.REMOTE_NODE_MULTIL_PARAMS,
        summary='get_all_followers',
        tags=['follows', RemoteUtil.REMOTE_IMPLEMENTED_TAG],
        responses=inline_serializer(
            name='Followers',
            fields={
                'type': serializers.CharField(),
                'items': AuthorSerializer(many=True)
            }
        )
    )
    def get(request: Request, author_id: str = None) -> HttpResponse:
        """
        Get followers for an Author

        See the step-by-step calls to follow or befriend someone at:
        https://github.com/hgshah/cmput404-project/blob/main/endpoints.txt#L137

        User story: As an author, my server will know about my friends
        """
        node_target, other_params = RemoteUtil.extract_node_target(request)
        if node_target is not None:
            return FollowersView.get_remote(request, node_target, other_params, author_id)

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
    def get_remote(request: Request, node_param: str, params: dict, author_id: str):
        node_config = base.REMOTE_CONFIG.get(node_param)
        if node_config is None:
            return HttpResponseNotFound()
        return node_config.get_all_followers_request(params, author_id)

    @staticmethod
    @extend_schema(
        parameters=RemoteUtil.REMOTE_NODE_MULTIL_PARAMS,
        summary='post_followers',
        tags=['follows', RemoteUtil.REMOTE_IMPLEMENTED_TAG],
        request=inline_serializer(
            name='FollowRequestRequest',
            fields={
                'actor': serializers.URLField(allow_null=True)
            }
        ),
        responses=FollowRequestSerializer(),
    )
    def post(request: Request, author_id: str = None) -> HttpResponse:
        """
        Create a follow request for an author

        There three are cases:
        1. A local author makes a follow request to a local author
            - Do an auth call with a user credential
            - author_id is the local author
        2. A remote node tells us that one of its users wants to follow us
            - Do an auth call with a node/server credential
            - Add an `actor` in the json payload in the request body
            - author_id is the local author they want to follow
        3. A local author makes a follow request to a remote author
            - Do an auth with a user credential
            - Add a node-target query param that should be equal to the remote server's domain
            - author_id is the remote author

        For more details, check out: https://github.com/hgshah/cmput404-project/pull/89

        User story: as an author: I want to un-befriend local and remote authors.

        User story: as an author, When I befriend someone (they accept my friend request) I follow them, only when the
        other author befriends me do I count as a real friend – a bi-directional follow is a true friend.

        See the step-by-step calls to follow or befriend someone at:
        https://github.com/hgshah/cmput404-project/blob/main/endpoints.txt#L137
        """
        if not request.user.is_authenticated:
            return HttpResponseNotFound()

        if request.user.is_authenticated_user:
            # let's figure out if we want to follow someone local or remote
            node_target, _ = RemoteUtil.extract_node_target(request)
            if node_target is None:
                return FollowersView.post_local_follow_local(request, author_id=author_id)
            else:
                return FollowersView.post_local_follow_remote(request, author_target_id=author_id,
                                                              node_target=node_target)

        if request.user.is_authenticated_node:
            # a remote node tells us that one of its users wants to follow someone in our server
            return FollowersView.post_remote_follow_local(request, author_id=author_id)

        return HttpResponseForbidden()

    @staticmethod
    def post_local_follow_local(request: Request, author_id: str = None) -> HttpResponse:
        actor: Author = request.user
        target = None
        data = None
        try:
            target = Author.objects.get(official_id=author_id)
            if target == actor:
                # validation: do not follow self!
                return HttpResponseBadRequest('You can not follow self')

            follow = Follow.objects.create(actor=actor.get_id(), target=target.get_id(), has_accepted=False)
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
    def post_local_follow_remote(request: Request, author_target_id: str, node_target: str) -> HttpResponse:
        node_config = base.REMOTE_CONFIG.get(node_target)
        if node_config is None:
            print(f"post_local_follow_remote: missing config: {node_target}")
            return HttpResponseNotFound()
        response_json = node_config.post_local_follow_remote(request.user.get_url(), author_target_id)
        if isinstance(response_json, int):
            return Response(status=response_json)
        try:
            actor_json = response_json['actor']
            target_json = response_json['object']
            follow = Follow.objects.create(
                actor=actor_json['url'],
                target=target_json['url'],
                has_accepted=response_json['hasAccepted'],
                remote_url=response_json['localUrl']
            )
            serializers = FollowRequestSerializer(follow)
            data = serializers.data
        except Author.DoesNotExist:
            return HttpResponseNotFound()
        except IntegrityError:
            return HttpResponseBadRequest('You\'re either following this account or have already made a follow request')
        except Exception as e:
            logger.error(f'FollowersView: post_local_follow_remote: post: unknown error: {e}')
            return HttpResponseBadRequest()
        return Response(data=data, status=201)

    @staticmethod
    def post_remote_follow_local(request: Request, author_id: str = None) -> HttpResponse:
        """
        a remote node tells us that one of its users wants to follow someone in our server

        payload should have author url of the author that wants to follow

        :param request:
        :param author_id:
        :return:
        """
        # todo: clean up code?
        target = None
        data = None
        try:
            author_actor_url = request.data['actor']
            target = Author.objects.get(official_id=author_id)
            follow = Follow.objects.create(actor=author_actor_url, target=target.get_id(), has_accepted=False)
            serializers = FollowRequestSerializer(follow)
            data = serializers.data
        except Author.DoesNotExist:
            print(f"Local author does not exist: {author_id}")
            return HttpResponseNotFound()
        except IntegrityError:
            return HttpResponseBadRequest('You\'re either following this account or have already made a follow request')
        except Exception as e:
            print(f'FollowersView: post: unknown error: {e}')
            return HttpResponseBadRequest()
        return Response(data=data, status=201)


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
        ),
        tags=['follows'],
        summary='get_all_real_friends'
    )
    def get(request: Request, author_id: str = None) -> HttpResponse:
        """
        Get mutual friends, real friends, true friends, or mutual followers for an Author

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
