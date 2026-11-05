import { Route, Routes } from 'react-router';

import { Layout } from './components/layout/Layout';
import { InputPage } from './pages/InputPage';
import { OverviewPage } from './pages/OverviewPage';

export function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<OverviewPage />} />
        <Route path="/input" element={<InputPage />} />
      </Routes>
    </Layout>
  );
}
