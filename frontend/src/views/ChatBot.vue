<template>
  <div class="app-container">
    <ConversationList
      :conversations="conversations"
      :activeConversationId="activeConversationId"
      @selectConversation="selectConversation"
      @addConversation="addConversation"
    />
    <ChatWindow
      v-if="activeConversation"
      :conversation="activeConversation"
      @sendMessage="sendMessage"
     current-user-id=""/>
    <div v-else class="no-conversation">
      <p>Select a conversation or add a new one to start chatting.</p>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue';
import ConversationList from '@/components/ConversationList.vue';
import ChatWindow from '@/components/ChatWindow.vue';
import api from "@/services/api";

export default {
  name: 'ChatBot',
  components: {
    ConversationList,
    ChatWindow,
  },
  setup() {
    const conversations = ref([
      {
        id: 1,
        name: 'Chat with Support',
        messages: [
          { sender: 'bot', text: 'Hello! How can I assist you today?' },
        ],
      },
      {
        id: 2,
        name: 'Chat with Sales',
        messages: [
          { sender: 'bot', text: 'Hi! Interested in our products?' },
        ],
      },
    ]);

    try {
      const response = api.get('/threads');
      this.message = response.data;
    } catch (err) {
      console.error(err);
    }

    const activeConversationId = ref(null);

    const selectConversation = (id) => {
      activeConversationId.value = id;
    };

    const addConversation = () => {
      const newId = conversations.value.length
        ? conversations.value[conversations.value.length - 1].id + 1
        : 1;
      const newConversation = {
        id: newId,
        name: `New Conversation ${newId}`,
        messages: [],
      };
      conversations.value.push(newConversation);
      activeConversationId.value = newId;
    };

    const activeConversation = computed(() =>
      conversations.value.find(
        (conv) => conv.id === activeConversationId.value
      )
    );

    const sendMessage = (text) => {
      if (activeConversation.value) {
        activeConversation.value.messages.push({
          sender: 'user',
          text,
        });
        // Simulate bot response
        setTimeout(() => {
          activeConversation.value.messages.push({
            sender: 'bot',
            text: `You said: "${text}"`,
          });
        }, 1000);
      }
    };

    return {
      conversations,
      activeConversationId,
      activeConversation,
      selectConversation,
      addConversation,
      sendMessage,
    };
  },
};
</script>

<style>
.app-container {
  display: flex;
  height: 100vh;
  font-family: Arial, sans-serif;
}

.no-conversation {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 1.2em;
  color: #555;
}
</style>
