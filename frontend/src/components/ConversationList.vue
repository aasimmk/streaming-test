<template>
  <div class="conversation-list">
    <h2>Conversations</h2>
    <ul>
      <li
        v-for="conversation in conversations"
        :key="conversation.id"
        :class="{ active: conversation.id === activeConversationId }"
        @click="$emit('selectConversation', conversation.id)"
      >
        {{ conversation.title }}
      </li>
    </ul>
    <button @click="addConversation">+ Add Conversation</button>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import api from '@/services/api';

export default {
  name: 'ConversationList',
  props: {
    activeConversationId: {
      type: Number,
      default: null,
    },
  },
  setup(props, { emit }) {
    const conversations = ref([]);

    const fetchConversations = async () => {
      try {
        const response = await api.get('/conversations/');
        conversations.value = response.data;
      } catch (error) {
        console.error('Error fetching conversations:', error);
      }
    };

    const addConversation = async () => {
      const title = prompt('Enter conversation title:');
      if (!title) return;

      try {
        const response = await api.post('/conversations/', {
          title,
          participant_ids: [], // Add participant IDs here
        });
        conversations.value.push(response.data);
        emit('selectConversation', response.data.id);
      } catch (error) {
        console.error('Error creating conversation:', error);
      }
    };

    onMounted(() => {
      fetchConversations();
    });

    return {
      conversations,
      addConversation,
    };
  },
};
</script>

<style scoped>
.conversation-list {
  width: 250px;
  border-right: 1px solid #ddd;
  padding: 20px;
  box-sizing: border-box;
  background-color: #f9f9f9;
}

.conversation-list h2 {
  margin-top: 0;
}

.conversation-list ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.conversation-list li {
  padding: 10px;
  margin-bottom: 5px;
  cursor: pointer;
  border-radius: 4px;
}

.conversation-list li.active {
  background-color: #007bff;
  color: white;
}

.conversation-list li:hover {
  background-color: #e6e6e6;
}

.conversation-list button {
  width: 100%;
  padding: 10px;
  margin-top: 10px;
  background-color: #28a745;
  border: none;
  color: white;
  border-radius: 4px;
  cursor: pointer;
}

.conversation-list button:hover {
  background-color: #218838;
}
</style>
