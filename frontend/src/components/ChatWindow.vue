<template>
  <div class="chat-window">
    <h2>Title - {{ conversation.name }}</h2>
    <div class="messages">
      <div
        v-for="(msg, index) in conversation.messages"
        :key="index"
        :class="['message', msg.sender]"
      >
        <span>{{ msg.text }}</span>
      </div>
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
import { ref } from 'vue';

export default {
  name: 'ChatWindow',
  props: {
    conversation: {
      type: Object,
      required: true,
    },
  },
  emits: ['sendMessage'],
  setup(props, { emit }) {
    const newMessage = ref('');

    const handleSubmit = () => {
      if (newMessage.value.trim() !== '') {
        emit('sendMessage', newMessage.value.trim());
        newMessage.value = '';
      }
    };

    return {
      newMessage,
      handleSubmit,
    };
  },
};
</script>

<style>
.chat-window {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 20px;
  box-sizing: border-box;
}

.chat-window h2 {
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
