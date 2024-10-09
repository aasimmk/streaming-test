<template>
  <div class="login-container">
    <h2>Login</h2>
    <form @submit.prevent="handleLogin">
      <div>
        <label for="username">Username:</label>
        <input v-model="username" type="text" id="username" required />
      </div>
      <div>
        <label for="password">Password:</label>
        <input v-model="password" type="password" id="password" required />
      </div>
      <div v-if="error" class="error">
        {{ error }}
      </div>
      <button type="submit">Login</button>
    </form>
  </div>
</template>

<script>
import api from '@/services/api';

export default {
  name: 'UserLogin',
  data() {
    return {
      username: '',
      password: '',
      error: null,
    };
  },
  methods: {
    async handleLogin() {
      this.error = null;
      try {
        const formData = new URLSearchParams();
        formData.append('username', this.username);
        formData.append('password', this.password);

        const response = await api.post('/login', formData, {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        });

        // Store the token in localStorage
        localStorage.setItem('access_token', response.data.access_token);

        // Redirect to protected route or home page
        this.$router.push('/dashboard');
      } catch (err) {
        if (err.response && err.response.data.detail) {
          this.error = err.response.data.detail;
        } else {
          this.error = 'An error occurred. Please try again.';
        }
      }
    },
  },
};
</script>

<style scoped>
.login-container {
  max-width: 400px;
  margin: 0 auto;
  padding: 2rem;
}

.error {
  color: red;
  margin-bottom: 1rem;
}
</style>
