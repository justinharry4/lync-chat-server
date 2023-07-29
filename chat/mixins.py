from rest_framework.response import Response
from rest_framework import status
from rest_framework.mixins import UpdateModelMixin

class CustomCreateModelMixin:
    def create(self, request, *args, **kwargs):
        create_serializer = self.get_serializer(data=request.data)
        create_serializer.is_valid(raise_exception=True)
        instance = create_serializer.save()

        retrieve_serializer = self.get_retrieve_serializer(instance)
        return Response(retrieve_serializer.data, status=status.HTTP_201_CREATED)
    

class CustomUpdateModelMixin(UpdateModelMixin):
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        update_serializer = self.get_serializer(instance, data=request.data, partial=partial)
        update_serializer.is_valid(raise_exception=True)
        mod_instance = update_serializer.save()
        
        retrieve_serializer = self.get_retrieve_serializer(mod_instance)
        return Response(retrieve_serializer.data, status=status.HTTP_200_OK)