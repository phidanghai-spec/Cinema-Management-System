from functools import wraps
from django.shortcuts import redirect
from cinema.repositories import UserRepository

def role_required(required_role):
    """
    Decorator to restrict view access to specific user roles.
    Injects the resolved user object as the second argument to the decorated function.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user_id = request.session.get('user_id')
            user = UserRepository.get_by_id(user_id) if user_id else None
            
            if user and user.role == required_role:
                return view_func(request, user, *args, **kwargs)
            
            # If not authorized
            if not user:
                return redirect('login')
            return redirect('index')
        return wrapper
    return decorator
