import { Routes, Route, Navigate } from 'react-router-dom';
import UnifiedPage from './pages/UnifiedPage';

function App() {
  return (
    <Routes>
      <Route path="/" element={<UnifiedPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
