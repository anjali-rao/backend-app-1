from django.contrib import admin

from earnings.models import Earning, Commission, Incentive
from utils.script import export_as_csv

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
    list_display = ('earning', 'updated')
    raw_id_fields = ('earning', 'application')
    fk_fields = ['earning', 'earning__user', 'earning__user__account',
    'earning__user__campaign', 'earning__user__enterprise', 'application',
    'application__proposer', 'application__quote',
    'application__proposer__user', 'application__proposer__user',
    'application__proposer__user__account', 'application__proposer__user__enterprise',
    'application__proposer__user__campaign', 'application__proposer__address',
    'application__proposer__address__pincode',
    'application__proposer__address__pincode__state',
    'application__quote__opportunity', 'application__quote__opportunity__lead',
    'application__quote__opportunity__lead__user',
    'application__quote__opportunity__lead__user__account',
    'application__quote__opportunity__lead__user__enterprise',
    'application__quote__opportunity__lead__user__campaign',
    'application__quote__opportunity__lead__contact',
    'application__quote__opportunity__lead__contact__address',
    'application__quote__opportunity__lead__contact__address__pincode',
    'application__quote__opportunity__lead__contact__address__pincode__state',
    'application__quote__opportunity__lead__category'
    ]
    actions = [export_as_csv]


@admin.register(Incentive)
class Incentive(admin.ModelAdmin):
    list_display = ('amount', 'criteria', 'updated')
    raw_id_fields = ('earning', 'application')
