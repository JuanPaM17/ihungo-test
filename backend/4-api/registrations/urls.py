from django.urls import path

from registrations.views import RegistrationRequestView

urlpatterns = [
    path("registro/", RegistrationRequestView.as_view(), name="registro"),
]
