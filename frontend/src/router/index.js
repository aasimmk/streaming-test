import { createRouter, createWebHistory } from 'vue-router';
import UserLogin from '@/views/UserLogin.vue';
import UserDashboard from '@/views/UserDashboard.vue';
import ChatBot from '@/views/ChatBot.vue';

const routes = [
  {
    path: '/',
    name: 'Home',
    redirect: '/login',
  },
  {
    path: '/login',
    name: 'UserLogin',
    component: UserLogin,
  },
  {
    path: '/dashboard',
    name: 'UserDashboard',
    component: UserDashboard,
    meta: { requiresAuth: true },
  },
  {
    path: '/chatbot',
    name: 'ChatBot',
    component: ChatBot,
    meta: { requiresAuth: true },
  },
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
});

router.beforeEach((to, from, next) => {
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth);
  const isAuthenticated = !!localStorage.getItem('access_token');

  if (requiresAuth && !isAuthenticated) {
    next('/login');
  } else {
    next();
  }
});

export default router;
