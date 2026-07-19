from django.urls import path

from .views import assessment_create

app_name = "governance"
urlpatterns = [path("use-case/<uuid:use_case_id>/new/", assessment_create, name="create")]
