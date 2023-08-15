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
    parent_models = []
    parent_url_lookups = []
    retrieve_serializer_class = None

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)

        if self.child:
            self.check_parent_existence()

    def get_parent_models(self):
        return self.parent_models
    
    def get_parent_url_lookups(self):
        return self.parent_url_lookups

    def get_retrieve_serializer(self, *args, **kwargs):
        if self.retrieve_serializer_class:
            return self.retrieve_serializer_class(*args, **kwargs)
        return self.get_serializer_class()(*args, **kwargs)
    
    def check_parent_existence(self):
        parent_models = self.get_parent_models()
        parent_url_lookups = self.get_parent_url_lookups()

        assert parent_models and parent_url_lookups, (
            '`.parent_models` and `.parent_url_lookups` attributes or '
            'the corresponding methods `.get_parent_models()` and '
            '`.get_parent_url_lookups()` must be set on child viewsets '
            'where `.child` is set to `True`'
        )

        parent_ids = [str(self.kwargs[lookup]) for lookup in parent_url_lookups]
        
        parent_objects = zip(parent_models, parent_ids)
        missing_objects = getattr(self, 'missing_objects', [])
        missing_parents = [
            (model, str(pk)) for model, pk
            in missing_objects if model in parent_models
        ]

        for parent_object in parent_objects:
            if parent_object not in missing_parents:
                model, pk = parent_object
                try:
                    model.objects.get(pk=pk)
                except model.DoesNotExist:
                    missing_parents.append(parent_object)

        errors = {}
        for model, pk in missing_parents:
            model_name = model.__name__.lower()
            errors[model_name] = f'parent with id `{pk}` was not found'

        if errors:
            raise NotFound(errors)


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