from django.contrib import admin

from his.framework.admin_sites import assign_custom_register, ManagementSite
from his.framework.configs import register_config

assign_custom_register(admin.site)
management_site = ManagementSite('management_site', 'users.SCREEN_/manage/')
register_config(management_site.orderly_register)
