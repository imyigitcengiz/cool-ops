from django.contrib import admin

from tools.models import FirmTag, MapsScrapedFirm, OutreachCollection, OutreachCollectionMember, WhatsappOutboundMessage


@admin.register(FirmTag)
class FirmTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'created_at')
    search_fields = ('name',)


@admin.register(MapsScrapedFirm)
class MapsScrapedFirmAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'messages_sent_count', 'last_scraped_at', 'last_message_at')
    search_fields = ('name', 'phone', 'address', 'place_id')
    list_filter = ('messages_sent_count', 'tags')
    filter_horizontal = ('tags',)


class OutreachCollectionMemberInline(admin.TabularInline):
    model = OutreachCollectionMember
    extra = 0


@admin.register(OutreachCollection)
class OutreachCollectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'skip_globally_messaged', 'allow_repeat_in_campaign', 'updated_at')
    search_fields = ('name',)
    inlines = [OutreachCollectionMemberInline]


@admin.register(WhatsappOutboundMessage)
class WhatsappOutboundMessageAdmin(admin.ModelAdmin):
    list_display = ('recipient_name', 'phone_display', 'status', 'collection', 'created_at', 'sent_at')
    list_filter = ('status', 'source')
    search_fields = ('recipient_name', 'phone_normalized', 'phone_display')
