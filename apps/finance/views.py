from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import widgets
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from apps.staffs.models import Staff
from django.contrib import messages
from django.http import JsonResponse
from apps.students.models import Student

from .forms import InvoiceItemFormset, InvoiceReceiptFormSet, Invoices
from .models import Invoice, InvoiceItem, Receipt, Due

from apps.corecode.views import staff_student_entry_restricted
from apps.corecode.models import Bill

class InvoiceListView(LoginRequiredMixin, ListView):
    model = Invoice


class InvoiceCreateView(LoginRequiredMixin, CreateView):
    model = Invoice
    fields = "__all__"
    success_url = "/finance/list"

    def get_context_data(self, **kwargs):
        context = super(InvoiceCreateView, self).get_context_data(**kwargs)
        if self.request.POST:
            context["items"] = InvoiceItemFormset(
                self.request.POST, prefix="invoiceitem_set"
            )
        else:
            context["items"] = InvoiceItemFormset(prefix="invoiceitem_set")
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context["items"]
        self.object = form.save()
        if self.object.id != None:
            if form.is_valid() and formset.is_valid():
                formset.instance = self.object
                formset.save()
        return super().form_valid(form)

def save_bill_details(request):
    bill = Bill.objects.get(id=1)
    last_receipt = Receipt.objects.last()
    #print(last_receipt.Bill_No)
    if request.method == 'POST':
        due = None
        student = request.POST.get('student')
        bill_number = request.POST.get('bill_number')
        bill_date = request.POST.get('bill_date')
        amount = request.POST.get('amount')
        re_by = request.POST.get('recived_by')
        comment = request.POST.get('comment')
        due_id = request.POST.get('due_id')
        next_due = request.POST.get('next_due_date')
        next_due_amount = request.POST.get('next_amount')
        if next_due_amount:
            next_due_amount = int(next_due_amount)
        if due_id:
            print("due id",due_id)   
            due = Due.objects.get(id=due_id)
        else:
            print("not found")
        print("staff id gotten: ",re_by)
        try:
            staff = Staff.objects.get(id=re_by)
        except Staff.DoesNotExist:
            messages.error(request, 'Error: Staff ID not found.')
            return redirect('bill')
        print("due date from view: ",next_due)
        invoice = Invoice.objects.get(student=student)
        if due is None:
            receipt = Receipt(
                Bill_No=bill_number,
                invoice=invoice,
                amount_paid=amount,
                date_paid=bill_date,
                comment=comment,
                received_by=staff
            )
        else:
            receipt = Receipt(
                Bill_No=bill_number,
                invoice=invoice,
                amount_paid=amount,
                date_paid=bill_date,
                comment=comment,
                received_by=staff,
                due=due
            )

        # Pass the extra arguments through the save method
        receipt.save(next_due_date=next_due, next_due_amount=next_due_amount)
        
       
       
        return redirect('bill')

    try:
        due = Due.objects.get(id = request.GET.get('due',None))
        return render(request, 'finance/bill.html',context={'stu':Student.objects.all(),'last_receipt':last_receipt,"bill":bill,"next_no":bill.last_bill+1,"due":due})
    except:
        return render(request, 'finance/bill.html',context={'stu':Student.objects.all(),'last_receipt':last_receipt,"bill":bill,"next_no":bill.last_bill+1,"due":"None"})

class InvoiceDetailView(LoginRequiredMixin, DetailView):
    model = Invoice
    fields = "__all__"

    def get_context_data(self, **kwargs):
        context = super(InvoiceDetailView, self).get_context_data(**kwargs)
        context["receipts"] = Receipt.objects.filter(invoice=self.object)
        context["items"] = InvoiceItem.objects.filter(invoice=self.object)
        return context


class InvoiceUpdateView(LoginRequiredMixin, UpdateView):
    model = Invoice
    fields = ["student"]

    def get_context_data(self, **kwargs):
        context = super(InvoiceUpdateView, self).get_context_data(**kwargs)
        if self.request.POST:
            context["receipts"] = InvoiceReceiptFormSet(
                self.request.POST, instance=self.object
            )
            context["items"] = InvoiceItemFormset(
                self.request.POST, instance=self.object
            )
        else:
            context["receipts"] = InvoiceReceiptFormSet(instance=self.object)
            context["items"] = InvoiceItemFormset(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context["receipts"]
        itemsformset = context["items"]
        if form.is_valid() and formset.is_valid() and itemsformset.is_valid():
            form.save()
            formset.save()
            itemsformset.save()
        return super().form_valid(form)


class InvoiceDeleteView(LoginRequiredMixin, DeleteView):
    model = Invoice
    success_url = reverse_lazy("invoice-list")


class ReceiptCreateView(LoginRequiredMixin, CreateView):
    model = Receipt
    fields = ["Bill_No","amount_paid", "date_paid", "comment"]
    success_url = reverse_lazy("invoice-list")
    def form_valid(self, form):
        obj = form.save(commit=False)
        invoice = Invoice.objects.get(pk=self.request.GET["invoice"])
        obj.invoice = invoice
        obj.save()
        return redirect("invoice-list")

    def get_context_data(self, **kwargs):
        context = super(ReceiptCreateView, self).get_context_data(**kwargs)
        invoice = Invoice.objects.get(pk=self.request.GET["invoice"])
        context["invoice"] = invoice
        return context


class ReceiptUpdateView(LoginRequiredMixin, UpdateView):
    model = Receipt
    fields = ["Bill_No","amount_paid", "date_paid", "comment"]
    success_url = reverse_lazy("invoice-list")


class ReceiptDeleteView(LoginRequiredMixin, DeleteView):
    model = Receipt
    success_url = reverse_lazy("invoice-list")


@login_required
def bulk_invoice(request):
    return render(request, "finance/bulk_invoice.html")




def get_student_dues(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    dues = Due.dues_for_student(student)
    invoice = Invoice.objects.get(student=student)
    if dues:
        dues_list = [{'amount': due.amount, 'due_date': due.due_date, 'id':due.id, "total_amount":due.invoice.total_amount_payable(),"balance":due.invoice.balance(),"paid":due.invoice.total_amount_paid()} for due in dues]
    else:
        dues_list = [{"total_amount":invoice.total_amount_payable(),"balance":invoice.balance(),"paid":invoice.total_amount_paid()}]
    return JsonResponse(dues_list, safe=False)




def dues_list(request):
    if request.method == "POST":
        dues = Due.objects.filter(invoice__student__student_name__icontains = request.POST.get("student_name"))
        return render(request,"finance/dues.html",{"dues":dues})
    dues = Due.objects.all()
    return render(request,"finance/dues.html",{"dues":dues})
    


def delete_due(request,**kwargs):
    pk = kwargs.get("pk")
    Due.objects.get(id=pk).delete()
    return redirect("due_dashboard")

def extend_due(request,**kwargs):
    if request.method == "POST":
        pk = kwargs.get("pk")
        date_to_extend = request.POST.get("new_due_date")
        due = Due.objects.get(id=pk)
        due.extend_due(date_to_extend)
        return redirect("due_dashboard")