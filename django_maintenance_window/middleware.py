# -*- coding: utf-8 -*-

from django.urls import reverse
from django.shortcuts import render
from django.utils.cache import add_never_cache_headers

from .conf import settings
from .models import MaintenanceMode


class MaintenanceModeMiddleware:
    """This middleware will check if the maintenance page should be shown."""
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        maintenance_response = self.check_maintenance(request)
        if maintenance_response:
            return maintenance_response

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response

    def check_maintenance(self, request):
        """
        This function will check if maintenance is activated.
        If so return the maintenance page.
        Otherwise continue the request.
        """
        config = MaintenanceMode.get_solo()

        if not config.maintenance:
            return None

        admin_root_url = reverse('admin:index')

        skip_maintenance = False
        if settings.MAINTENANCE_EXCLUDE_ADMIN_URLS and request.path.startswith(admin_root_url):
            skip_maintenance = True
        if settings.MAINTENANCE_EXCLUDE_SUPER_USER and request.user and request.user.is_superuser:
            skip_maintenance = True
        if settings.MAINTENANCE_EXCLUDE_STAFF_USER and request.user and request.user.is_staff:
            skip_maintenance = True

        for exclude_url in settings.MAINTENANCE_EXCLUDE_URLS:
            if request.path.startswith(exclude_url):
                skip_maintenance = True
                break

        if not skip_maintenance:
            kwargs = {
                'end_date': config.maintenance_until,
                'display_end_date': settings.MAINTENANCE_DISPLAY_END_DATE
            }

            response = render(
                request, settings.MAINTENANCE_TEMPLATE,
                content_type='text/html', status=503, context=kwargs)
            add_never_cache_headers(response)
            return response
        return None
