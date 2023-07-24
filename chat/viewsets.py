from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins


class NoUpdateModelViewSet(mixins.ListModelMixin,
                           mixins.CreateModelMixin,
                           mixins.RetrieveModelMixin,
                           mixins.DestroyModelMixin,
                           GenericViewSet):
    """
    Generic viewset providing list, create, retrieve and destroy functionality.
    """
    pass