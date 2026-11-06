import { Navigate, Route, Routes } from 'react-router';

import { Layout } from './components/layout/Layout';
import { InputPage } from './pages/InputPage';
import { MonitorPage } from './pages/MonitorPage';
import { OverviewPage } from './pages/OverviewPage';

export function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<OverviewPage />} />
        <Route path="/input" element={<InputPage />} />
        <Route path="/questions" element={<Navigate to="/input" replace />} />
        <Route path="/monitor" element={<MonitorPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}
