import { Routes, Route } from 'react-router-dom';
import { Layout } from './components';
import { DashboardPage, AuthPage, DownloadPage, BatchPage } from './pages';

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/auth" element={<AuthPage />} />
        <Route path="/download" element={<DownloadPage />} />
        <Route path="/batch" element={<BatchPage />} />
      </Routes>
    </Layout>
  );
}

export default App;
