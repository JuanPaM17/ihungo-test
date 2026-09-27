from django.urls import path

from bulk_upload.views import BulkUploadActividadesView, BulkUploadAsociadosView

urlpatterns = [
    path("carga-masiva/asociados/", BulkUploadAsociadosView.as_view()),
    path("carga-masiva/actividades/", BulkUploadActividadesView.as_view()),
]
