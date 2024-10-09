<template>
  <div class="app-container">
    <ConversationList
      :conversations="conversations"
      :activeConversationId="activeConversationId"
      @selectConversation="selectConversation"
      @addConversation="addConversation"
    />
    <div class="chat-section">
      <router-view></router-view>
    </div>
    <button class="logout-button" @click="handleLogout">Logout</button>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import ConversationList from '@/components/ConversationList.vue';
import api from '@/services/api';

export default {
  name: 'ChatBot',
  components: {
    ConversationList,
  },
  setup() {
    const router = useRouter();
    const conversations = ref([]);
    const activeConversationId = ref(null);

    const fetchConversations = async () => {
      try {
        const response = await api.get('/conversations/');
        conversations.value = response.data;
      } catch (error) {
        console.error('Error fetching conversations:', error);
      }
    };

    const selectConversation = (id) => {
      activeConversationId.value = id;
      router.push(`/chatbot/${id}`);
    };

    const addConversation = async () => {
      const title = prompt('Enter conversation title:');
      if (!title) return;

      try {
        const response = await api.post('/conversations/', {
          title,
          participant_ids: [],
        });
        conversations.value.push(response.data);
        selectConversation(response.data.id);
      } catch (error) {
        console.error('Error creating conversation:', error);
      }
    };

    const handleLogout = () => {
      localStorage.removeItem('access_token');
      router.push('/login');
    };

    onMounted(() => {
      fetchConversations();
    });

    return {
      conversations,
      activeConversationId,
      selectConversation,
      addConversation,
      handleLogout,
    };
  },
};
</script>

<style scoped>
.app-container {
  display: flex;
  height: 100vh;
  position: relative;
  font-family: Arial, sans-serif;
}

/* Conversation List Styling */
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

/* Chat Section Styling */
.chat-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
}

/* Logout Button Styling */
.logout-button {
  position: absolute;
  top: 20px;
  right: 20px;
  padding: 8px 16px;
  background-color: #dc3545;
  border: none;
  color: white;
  border-radius: 4px;
  cursor: pointer;
}

.logout-button:hover {
  background-color: #c82333;
}
</style>
