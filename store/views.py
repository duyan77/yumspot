from store.models import Restaurant, User  # Import model của bạn


def dashboard_callback(request, context):
    context.update({
        "user_count": User.objects.count(),
        "restaurant_count": Restaurant.objects.count(),
    })
    return context

