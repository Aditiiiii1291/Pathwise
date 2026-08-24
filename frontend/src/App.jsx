import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import OverviewPage from './pages/OverviewPage';
import StudentsPage from './pages/StudentsPage';
import StudentProfilePage from './pages/StudentProfilePage';
import RulesPage from './pages/RulesPage';
import UploadPage from './pages/UploadPage';
import LoginPage from './pages/LoginPage';
import NotFoundPage from './pages/NotFoundPage';
import ConnectionStatusPage from './pages/ConnectionStatusPage';
import { checkHealth } from './utils/api';

export default function App() {
  const [startupStatus, setStartupStatus] = useState('checking'); // 'checking' | 'connected' | 'unavailable'
  const [serviceInfo, setServiceInfo] = useState(null);

  const verifyStartupHealth = async () => {
    setStartupStatus('checking');
    try {
      const res = await checkHealth();
      if (res && res.status === 'healthy') {
        setServiceInfo(res.service || 'pathwise-api');
        setStartupStatus('connected');
      } else {
        setStartupStatus('unavailable');
      }
    } catch {
      setStartupStatus('unavailable');
    }
  };

  useEffect(() => {
    verifyStartupHealth();
  }, []);

  // 1. Initial startup loading / checking screen
  if (startupStatus === 'checking') {
    return (
      <ConnectionStatusPage
        status="checking"
        serviceInfo={serviceInfo}
        onRetry={verifyStartupHealth}
      />
    );
  }

  // 2. Initial startup unavailable connection screen
  if (startupStatus === 'unavailable') {
    return (
      <ConnectionStatusPage
        status="unavailable"
        serviceInfo={serviceInfo}
        onRetry={verifyStartupHealth}
      />
    );
  }

  // 3. Connected application with full router
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<Layout />}>
          <Route index element={<OverviewPage />} />
          <Route path="students" element={<StudentsPage />} />
          <Route path="students/:id" element={<StudentProfilePage />} />
          <Route path="rules" element={<RulesPage />} />
          <Route path="upload" element={<UploadPage />} />
        </Route>
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  );
}
