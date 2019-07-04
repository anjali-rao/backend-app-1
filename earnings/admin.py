from django.contrib import admin

from earnings.models import Earning, Commission, Incentive


class CommissionInline(admin.StackedInline):
    model = Commission
    can_delete = False


class IncentiveInline(admin.StackedInline):
    model = Incentive
    can_delete = False


@admin.register(Earning)
class EarningAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'earning_type', 'status')
    raw_id_fields = ('user',)
    search_fields = ('user__account__phone_no', 'quote__id')
    list_filter = ('status',)
    _inlines_class_set = dict(
        commission=CommissionInline,
        incentive=IncentiveInline
    )

    def get_inline_instances(self, request, obj=None):
        inlines = list()
        if obj is not None and hasattr(obj, obj.earning_type):
            inline_class = self.get_inline_class(obj.earning_type)
            inlines.append(inline_class(self.model, self.admin_site))
        return inlines

    def get_inline_class(self, keywords):
        return self._inlines_class_set.get(keywords)


@admin.register(Commission)
class CommisionAdmin(admin.ModelAdmin):
    list_display = ('earning', 'application', 'updated')
    raw_id_fields = ('earning', 'application')


@admin.register(Incentive)
class Incentive(admin.ModelAdmin):
    list_display = ('amount', 'criteria', 'updated')
    raw_id_fields = ('earning', 'application')
