from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins
from rest_framework.exceptions import NotFound

from .mixins import CustomCreateModelMixin, CustomUpdateModelMixin


class CustomGenericViewSet(GenericViewSet):
    """
    This class defines generic view behaviour such as `.get_retrieve_serialzer()`
    which is used in generic viewsets with support for custom writes, and 
    `.check_parent_existence()` which is used for strict parent existence checks
    in child viewsets where the `.child` attribute is set to `True`.
    """

    child = False
    parent_model = None
    parent_url_lookup = None
    retrieve_serializer_class = None

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)

        if self.child:
            self.check_parent_existence()

    def get_retrieve_serializer(self, *args, **kwargs):
        if self.retrieve_serializer_class:
            return self.retrieve_serializer_class(*args, **kwargs)
        return self.get_serializer_class()(*args, **kwargs)
    
    def check_parent_existence(self):
        assert self.parent_model and self.parent_url_lookup, (
            '`.parent_model` and `.parent_url_lookup` attributes must '
            'be set on child viewsets where `.child` is set to `True`'
        )

        parent_model = self.parent_model
        parent_id = self.kwargs[self.parent_url_lookup]

        parent_object = (parent_model, str(parent_id))
        missing_objects = getattr(self, 'missing_objects', [])
        missing_parents = [(model, str(pk)) for model, pk in missing_objects
                           if model == parent_model]
        
        if parent_object not in missing_parents:
            missing_parents.append(parent_object)

        for model, pk in missing_parents:
            try:
                model.objects.get(pk=pk)
            except model.DoesNotExist:
                raise NotFound(
                    f'parent {model.__name__} with id `{pk}` was not found'
                )


class ReadOnlyModelViewSet(mixins.ListModelMixin,
                           mixins.RetrieveModelMixin,
                           CustomGenericViewSet):
    pass


class ModelViewSet(mixins.ListModelMixin,
                   mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.UpdateModelMixin,
                   mixins.DestroyModelMixin,
                   CustomGenericViewSet):
    pass


class NoUpdateModelViewSet(mixins.ListModelMixin,
                           mixins.CreateModelMixin,
                           mixins.RetrieveModelMixin,
                           mixins.DestroyModelMixin,
                           CustomGenericViewSet):
    """
    Generic viewset providing list, create, retrieve and destroy functionality.
    """
    pass


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