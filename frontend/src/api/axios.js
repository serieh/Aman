import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access');
  // Do not attach the token for login or register endpoints
  const isAuthRequest = config.url && (config.url.includes('/auth/login') || config.url.includes('/auth/register'));
  if (token && !isAuthRequest) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// Handle 401 Unauthorized errors automatically
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response && error.response.status === 401 && !originalRequest._retry) {
      if (originalRequest.url && originalRequest.url.includes('/auth/refresh')) {
          localStorage.removeItem('access');
          localStorage.removeItem('refresh');
          if (window.location.pathname !== '/login' && window.location.pathname !== '/') {
            window.location.href = '/login';
          }
          return Promise.reject(error);
      }

      if (isRefreshing) {
        return new Promise(function(resolve, reject) {
          failedQueue.push({resolve, reject});
        }).then(token => {
          originalRequest.headers['Authorization'] = 'Bearer ' + token;
          return api(originalRequest);
        }).catch(err => {
          return Promise.reject(err);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = localStorage.getItem('refresh');
      if (!refreshToken) {
         isRefreshing = false;
         localStorage.removeItem('access');
         if (window.location.pathname !== '/login' && window.location.pathname !== '/') {
           window.location.href = '/login';
         }
         return Promise.reject(error);
      }

      try {
        const { data } = await axios.post('/api/v1/auth/refresh/', { refresh: refreshToken });
        const newAccess = data.access;
        localStorage.setItem('access', newAccess);
        if (data.refresh) {
             localStorage.setItem('refresh', data.refresh);
        }
        api.defaults.headers.common['Authorization'] = 'Bearer ' + newAccess;
        originalRequest.headers['Authorization'] = 'Bearer ' + newAccess;
        processQueue(null, newAccess);
        return api(originalRequest);
      } catch (err) {
        processQueue(err, null);
        localStorage.removeItem('access');
        localStorage.removeItem('refresh');
        if (window.location.pathname !== '/login' && window.location.pathname !== '/') {
          window.location.href = '/login';
        }
        return Promise.reject(err);
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(error);
  }
);

export default api;
