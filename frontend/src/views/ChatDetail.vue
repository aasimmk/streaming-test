<template>
  <div class="chat-detail">
    <h2>Chat Title: {{ conversation.title }}</h2>
    <div class="messages">
      <div
        v-for="(message, index) in messages"
        :key="index"
        :class="['message', message.sender_id === 'bot' ? 'user' : 'bot']"
      >
        <span>Query: {{ message.content }}</span>
        <div v-if="message.response" :class="['message', 'user', 'archived']">
          <span>{{ message.response }}</span>
        </div>
      </div>
      <div
        v-if="responseMessage!==''"
        :class="['message', 'user']"
      >
        <span>{{ responseMessage }}</span>
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
  data() {
    return {
      socket: null,
      responseMessage: '',
    }
  },
  mounted() {
    this.socket = new WebSocket('ws://localhost:8000/stream');
  },
  methods: {
    async createMessage(){
      if (this.conversation.id === 'undefined') return;
      const response = await api.post(`/conversations/${this.conversation.id}/messages/`, {
        content: this.newMessage.trim(),
      });
      this.messages.push(response.data);
      this.newMessage = '';
      console.log("Message added >>>>>>  " + JSON.stringify(response.data));
      return response.data;
    },
    async handleSubmit() {
      // Add message
      const createdMessageData = await this.createMessage();
      createdMessageData['access_token'] = localStorage.getItem('access_token');
      createdMessageData['conversation_id'] = this.conversation.id;

      // Send data to WS
      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        console.log("Sending to WS >>>>>>  " + JSON.stringify(createdMessageData));
        this.socket.send(JSON.stringify(createdMessageData));
        this.responseMessage = '';
        this.newMessage = ''
      }
      this.socket.onmessage = (event) => {
        this.responseMessage += event.data;
      }
      this.socket.onclose = () => {
        console.log('Socket onclosed called')
        this.socket = null;
        this.messages.push({ sender_id: 'bot', content: this.responseMessage });
        this.responseMessage = '';
      }
    }
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

.message.archived {
  margin-left: -6px;
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
