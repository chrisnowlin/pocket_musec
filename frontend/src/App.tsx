import { Routes, Route, Navigate } from 'react-router-dom';
import UnifiedPage from './pages/UnifiedPage';
import PocketPlannerPage from './pages/PocketPlannerPage';
import MusecDBPage from './pages/MusecDBPage';
import MusecTrackerPage from './pages/MusecTrackerPage';

function App() {
  return (
    <Routes>
      <Route path="/" element={<UnifiedPage />} />
      <Route path="/planner" element={<PocketPlannerPage />} />
      <Route path="/db" element={<MusecDBPage />} />
      <Route path="/tracker" element={<MusecTrackerPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
