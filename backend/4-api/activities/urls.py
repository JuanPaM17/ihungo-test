from rest_framework.routers import DefaultRouter

from activities.views import ActivityViewSet

router = DefaultRouter()
router.register("actividades", ActivityViewSet, basename="actividad")

urlpatterns = router.urls
