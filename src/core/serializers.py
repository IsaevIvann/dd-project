from rest_framework import serializers

class LinkChatSerializer(serializers.Serializer):
    order_id = serializers.IntegerField(required=False)
    phone = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    chat_id = serializers.CharField(max_length=32)
