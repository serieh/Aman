import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './store/useAuthStore';
import AuthPage from './pages/AuthPage';
import Dashboard from './pages/Dashboard';
import ChatRoom from './pages/ChatRoom';
import AppLayout from './layouts/AppLayout';

function PrivateRoute({ children }) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  return isAuthenticated ? children : <Navigate to="/login" replace />;
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<AuthPage />} />
      <Route path="/" element={<PrivateRoute><AppLayout /></PrivateRoute>}>
        <Route index element={<Dashboard />} />
        <Route path="chat" element={<Navigate to="/" replace />} />
        <Route path="chat/:chatId" element={<ChatRoom />} />
      </Route>
    </Routes>
  );
}

export default App;
