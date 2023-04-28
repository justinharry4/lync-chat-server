from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, AllowAny


def api_view_method(*args, perm_classes=[AllowAny], **kwargs):
    """
    Decorator to be applied to class-based view methods.
    Behaves like the `api_view` decorator for function-based
    views. 
    """

    def decorator(func):
        @api_view(*args, **kwargs)
        @permission_classes(perm_classes)
        def view_func(*view_args, **view_kwargs):
            instance = APIView()
            response = func(instance, *view_args, **view_kwargs)
            return response
        
        return view_func
    
    return decorator

