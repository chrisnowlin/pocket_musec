import { Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import DashboardPage from './pages/DashboardPage';
import ImagesPage from './pages/ImagesPage';
import SettingsPage from './pages/SettingsPage';
import IngestionPage from './pages/IngestionPage';
import UnifiedPage from './pages/UnifiedPage';
import WorkspaceShell from './workspace/WorkspaceShell';

function App() {
  return (
    <Routes>
      <Route path="/" element={<UnifiedPage />} />

      {/* Legacy interface moved under /classic */}
      <Route path="classic" element={<Layout />}>
        <Route index element={<DashboardPage />} />
        <Route path="images" element={<ImagesPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="ingestion" element={<IngestionPage />} />
      </Route>

      <Route path="workspace" element={<Navigate to="/" replace />} />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
