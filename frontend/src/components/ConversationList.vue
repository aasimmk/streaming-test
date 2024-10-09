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
        Chat {{ conversation.id }}
      </li>
    </ul>
    <button @click="$emit('addConversation')">+ Add Conversation</button>
  </div>
</template>

<script>
export default {
  name: 'ConversationList',
  props: {
    conversations: {
      type: Array,
      required: true,
    },
    activeConversationId: {
      type: Number,
      default: null,
    },
  },
};
</script>

<style>
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
