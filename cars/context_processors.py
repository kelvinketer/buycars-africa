from .models import Conversation, Message
from django.db.models import Count, Q

def unread_messages_count(request):
    """
    Returns the count of unread messages for the logged-in user.
    Available in all templates as {{ unread_count }}.
    """
    if request.user.is_authenticated:
        # Count messages where:
        # 1. The user is a participant in the conversation
        # 2. The sender is NOT the user (incoming messages)
        # 3. is_read is False
        
        count = Message.objects.filter(
            conversation__in=Conversation.objects.filter(
                Q(buyer=request.user) | Q(dealer=request.user)
            ),
            is_read=False
        ).exclude(sender=request.user).count()
        
        return {'unread_count': count}
    
    return {'unread_count': 0}