from rest_framework.routers import DefaultRouter

from users.views import AsociadoViewSet

router = DefaultRouter()
router.register("asociados", AsociadoViewSet, basename="asociado")

urlpatterns = router.urls
