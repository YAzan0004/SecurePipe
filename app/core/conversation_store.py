from typing import Dict, List


# تخزين المحادثات مؤقتًا داخل الذاكرة
class ConversationStore:
    def __init__(self, max_messages: int = 10):
        self.conversations: Dict[str, List[dict]] = {}
        self.max_messages = max_messages

    # جلب سجل محادثة معيّنة
    def get_history(self, conversation_id: str) -> List[dict]:
        return self.conversations.get(conversation_id, [])

    # إضافة رسالة جديدة للمحادثة
    def add_message(self, conversation_id: str, role: str, content: str):
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []

        self.conversations[conversation_id].append({
            "role": role,
            "content": content
        })

        # الاحتفاظ بآخر عدد محدد من الرسائل فقط
        self.conversations[conversation_id] = self.conversations[conversation_id][-self.max_messages:]

    # حذف سجل محادثة معيّنة
    def clear_history(self, conversation_id: str):
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]


# إنشاء كائن واحد لاستخدامه في النظام
conversation_store = ConversationStore(max_messages=10)