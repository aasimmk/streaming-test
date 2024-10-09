<template>
  <div class="dashboard">
    <h2>Dashboard</h2>
    <p>{{ message }}</p>
    <button @click="logout">Logout</button>
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
