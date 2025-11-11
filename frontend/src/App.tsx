import { Routes, Route, Navigate } from 'react-router-dom';
import DashboardPage from './pages/DashboardPage';
import ImagesPage from './pages/ImagesPage';
import SettingsPage from './pages/SettingsPage';
import UsersPage from './pages/UsersPage';
import Layout from './components/Layout';

function App() {
  return (
    <Routes>
      <Route
        path="/"
        element={<Layout />}
      >
        <Route index element={<DashboardPage />} />
        <Route path="images" element={<ImagesPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="users" element={<UsersPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
