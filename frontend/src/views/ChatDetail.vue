<template>
  <div class="chat-detail">
    <h2>{{ conversation.title }}</h2>
    <div class="messages">
      <div
        v-for="message in messages"
        :key="message.id"
        :class="['message', message.sender_id === currentUserId ? 'user' : 'bot']"
      >
        <span>{{ message.content }}</span>
      </div>
      <div ref="messagesEnd"></div>
    </div>
    <form @submit.prevent="handleSubmit" class="message-input">
      <input
        type="text"
        v-model="newMessage"
        placeholder="Type your message..."
        required
      />
      <button type="submit">Send</button>
    </form>
  </div>
</template>

<script>
import { ref, onMounted, watch, nextTick } from 'vue';
import { useRoute } from 'vue-router';
import api from '@/services/api';

export default {
  name: 'ChatDetail',
  props: {
    currentUserId: {
      type: Number,
      required: true,
    },
  },
  setup() {
    const route = useRoute();
    const conversation = ref({});
    const messages = ref([]);
    const newMessage = ref('');
    const messagesEnd = ref(null);

    const fetchConversation = async () => {
      try {
        const response = await api.get(`/conversations/${route.params.conversation_id}`);
        conversation.value = response.data;
        messages.value = response.data.messages;
        scrollToBottom();
      } catch (error) {
        console.error('Error fetching conversation:', error);
      }
    };

    const handleSubmit = async () => {
      if (!newMessage.value.trim()) return;

      try {
        messages.value.push(newMessage.value.trim());
        const message_response = await api.post(`/conversations/${conversation.value.id}/messages/`, {
          content: newMessage.value.trim(),
        });
        console.log(message_response);
        // const query_response = await api.post(`/conversations/${conversation.value.id}/query/`, {
        //   content: newMessage.value.trim(),
        // });
        // messages.value.push(query_response.data);
        newMessage.value = '';
        scrollToBottom();
      } catch (error) {
        console.error('Error sending message:', error);
      }
    };

    const scrollToBottom = () => {
      nextTick(() => {
        if (messagesEnd.value) {
          messagesEnd.value.scrollIntoView({ behavior: 'smooth' });
        }
      });
    };

    watch(
      () => route.params.conversation_id,
      () => {
        fetchConversation();
      }
    );

    onMounted(() => {
      fetchConversation();
    });

    return {
      conversation,
      messages,
      newMessage,
      handleSubmit,
      messagesEnd,
    };
  },
};
</script>

<style scoped>
.chat-detail {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 20px;
  box-sizing: border-box;
  position: relative;
}

.chat-detail h2 {
  margin-top: 0;
  border-bottom: 1px solid #ddd;
  padding-bottom: 10px;
}

.messages {
  flex: 1;
  overflow-y: auto;
  margin: 20px 0;
}

.message {
  padding: 10px;
  margin-bottom: 10px;
  border-radius: 4px;
  max-width: 70%;
}

.message.user {
  background-color: #dcf8c6;
  align-self: flex-end;
}

.message.bot {
  background-color: #f1f0f0;
  align-self: flex-start;
}

.message-input {
  display: flex;
  border-top: 1px solid #ddd;
  padding-top: 10px;
}

.message-input input {
  flex: 1;
  padding: 10px;
  font-size: 1em;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.message-input button {
  padding: 10px 20px;
  margin-left: 10px;
  background-color: #007bff;
  border: none;
  color: white;
  border-radius: 4px;
  cursor: pointer;
}

.message-input button:hover {
  background-color: #0069d9;
}
</style>
