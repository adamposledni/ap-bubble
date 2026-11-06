import { Route, Routes } from 'react-router';

import { Layout } from './components/layout/Layout';
import { InputPage } from './pages/InputPage';
import { MonitorPage } from './pages/MonitorPage';
import { OverviewPage } from './pages/OverviewPage';
import { QuestionsPage } from './pages/QuestionsPage';

export function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<OverviewPage />} />
        <Route path="/input" element={<InputPage />} />
        <Route path="/questions" element={<QuestionsPage />} />
        <Route path="/monitor" element={<MonitorPage />} />
      </Routes>
    </Layout>
  );
}
