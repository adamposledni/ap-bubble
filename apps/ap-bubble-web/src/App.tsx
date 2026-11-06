import { Route, Routes } from 'react-router';

import { Layout } from './components/layout/Layout';
import { InputPage } from './pages/InputPage';
import { KnowledgeDocPage } from './pages/KnowledgeDocPage';
import { KnowledgePage } from './pages/KnowledgePage';
import { MonitorPage } from './pages/MonitorPage';
import { OverviewPage } from './pages/OverviewPage';

export function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<OverviewPage />} />
        <Route path="/knowledge" element={<KnowledgePage />} />
        <Route path="/knowledge/:folder/:slug" element={<KnowledgeDocPage />} />
        <Route path="/input" element={<InputPage />} />
        <Route path="/monitor" element={<MonitorPage />} />
      </Routes>
    </Layout>
  );
}
