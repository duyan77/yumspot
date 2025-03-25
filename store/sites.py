# sites.py
from django.shortcuts import render
from django.template.response import TemplateResponse
from django.urls import path
from unfold.sites import UnfoldAdminSite


class CustomAdminSite(UnfoldAdminSite):
	site_header = "Yumspot Admin"
	site_title = "Yumspot Admin Panel"
	index_title = "Welcome to Yumspot Admin"

	def get_urls(self):
		urls = super().get_urls()
		custom_urls = [
			path("stats/", self.admin_view(self.stats_view), name="admin_stats"),
			# Định nghĩa đường dẫn /admin/stats
		]
		return custom_urls + urls

	def stats_view(self, request):
		context = self.each_context(request)  # Lấy context chung của admin
		return TemplateResponse(request, "admin/index.html", context)


custom_admin_site = CustomAdminSite(name="custom_admin")
