<template>
  <div class="dashboard container mt-5">
    <div class="row justify-content-center">
      <div class="col-6 text-center">
        <h2 class="mb-4">Dashboard</h2>
        <p class="mb-3">{{ message }}</p>
        <button class="btn btn-primary mb-3" @click="logout">Logout</button>

        <router-link to="/chatbot" class="btn btn-secondary">Go to Chatbot</router-link>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api';

export default {
  name: 'UserDashboard',
  data() {
    return {
      message: '',
    };
  },
  async created() {
    try {
      const response = await api.get('/protected-route');
      this.message = response.data.message;
    } catch (err) {
      console.error(err);
      this.$router.push('/login');
    }
  },
  methods: {
    logout() {
      localStorage.removeItem('access_token');
      this.$router.push('/login');
    },
  },
};
</script>

<style scoped>
.dashboard {
  padding: 2rem;
}
</style>
