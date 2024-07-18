from django.contrib.messages.views import SuccessMessageMixin
from django.forms import widgets
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django import forms
import os
from .models import Staff
from django.utils.decorators import method_decorator
from apps.corecode.views import staff_student_entry_restricted,different_user_restricted
from apps.corecode.models import User

class StaffListView(ListView):
    model = Staff

@method_decorator(different_user_restricted(),name='dispatch')
class StaffDetailView(DetailView):
    model = Staff
    template_name = "staffs/staff_detail.html"
    

@method_decorator(staff_student_entry_restricted(),name='dispatch')
class StaffCreateView(SuccessMessageMixin, CreateView):
    model = Staff
    fields = "__all__"
    success_message = "New staff successfully added"

    def get_form(self):
        """add date picker in forms"""
        form = super(StaffCreateView, self).get_form()
        del form.fields["user"]
        if self.request.user.is_staff and not self.request.user.is_superuser:
            del form.fields["username"]
            del form.fields["password"]
        form.fields["date_of_birth"].widget = widgets.DateInput(attrs={"type": "date"})
        form.fields["date_of_admission"].widget = widgets.DateInput(
            attrs={"type": "date"}
        )
        form.fields["address"].widget = widgets.Textarea(attrs={"rows": 1})
        form.fields["working_exp"].widget = widgets.Textarea(attrs={"rows": 1})
        return form
    def form_valid(self, form):
        # Handle file uploads here
        form.instance.passport = self.request.FILES.get('passport')
        form.instance.aadhar_card = self.request.FILES.get('aadhar_card')
        form.instance.degree_certificate = self.request.FILES.get('degree_certificate')
        form.instance.resume = self.request.FILES.get('resume')
        return super().form_valid(form)
    


@method_decorator(staff_student_entry_restricted(),name='dispatch')
class StaffUpdateView(SuccessMessageMixin, UpdateView):
    model = Staff
    fields = "__all__"
    success_message = "Record successfully updated."

    def get_form(self):
        """add date picker in forms"""
        form = super(StaffUpdateView, self).get_form()
        del form.fields["user"]
        if self.request.user.is_staff and not self.request.user.is_superuser:
            del form.fields["username"]
            del form.fields["password"]
        form.fields["date_of_birth"].widget = widgets.DateInput(attrs={"type": "date"})
        form.fields["date_of_admission"].widget = widgets.DateInput(
            attrs={"type": "date"}
        )
        form.fields["address"].widget = widgets.Textarea(attrs={"rows": 1})
        form.fields["working_exp"].widget = widgets.Textarea(attrs={"rows": 1})
        return form
    def form_valid(self, form):
        # Handle file uploads here
        form.instance.passport = self.request.FILES.get('passport')
        form.instance.aadhar_card = self.request.FILES.get('aadhar_card')
        form.instance.degree_certificate = self.request.FILES.get('degree_certificate')
        form.instance.resume = self.request.FILES.get('resume')
        return super().form_valid(form)
    def save(self, *args, **kwargs):
        # Delete previous images before saving new ones
        if self.pk:
            original = Staff.objects.get(pk=self.pk)
            if self.passport and original.passport != self.passport:
                if os.path.isfile(original.passport.path):
                    os.remove(original.passport.path)
            if self.aadhar_card and original.aadhar_card != self.aadhar_card:
                if os.path.isfile(original.aadhar_card.path):
                    os.remove(original.aadhar_card.path)
            if self.degree_certificate and original.degree_certificate != self.degree_certificate:
                if os.path.isfile(original.degree_certificate.path):
                    os.remove(original.degree_certificate.path)
            if self.resume and original.resume != self.resume:
                if os.path.isfile(original.resume.path):
                    os.remove(original.resume.path)
        super().save(*args, **kwargs)


@method_decorator(staff_student_entry_restricted(),name='dispatch')
class StaffDeleteView(DeleteView):
    model = Staff
    success_url = reverse_lazy("staff-list")
