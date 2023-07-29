from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins

from .mixins import CustomCreateModelMixin, CustomUpdateModelMixin

class NoUpdateModelViewSet(mixins.ListModelMixin,
                           mixins.CreateModelMixin,
                           mixins.RetrieveModelMixin,
                           mixins.DestroyModelMixin,
                           GenericViewSet):
    """
    Generic viewset providing list, create, retrieve and destroy functionality.
    """
    pass



class CustomGenericViewSet(GenericViewSet):
    retrieve_serializer_class = None

    def get_retrieve_serializer(self, *args, **kwargs):
        if self.retrieve_serializer_class:
            return self.retrieve_serializer_class(*args, **kwargs)
        return self.get_serializer_class()(*args, **kwargs)


class CustomWriteModelViewSet(mixins.ListModelMixin,
                              mixins.RetrieveModelMixin,
                              mixins.DestroyModelMixin,
                              CustomCreateModelMixin,
                              CustomUpdateModelMixin,
                              CustomGenericViewSet):
    """
    Generic viewset providing list, create, retrieve, update and destroy functionality
    with support for custom serializer interfaces for create and update actions.
    """
    pass


class CustomWriteNoUpdateModelViewSet(mixins.ListModelMixin,
                                      mixins.RetrieveModelMixin,
                                      mixins.DestroyModelMixin,
                                      CustomCreateModelMixin,
                                      CustomGenericViewSet):
    """
    Generic viewset providing list, create, retrieve and destroy functionality
    with support for a custom serializer interface for the create action.
    """
    pass