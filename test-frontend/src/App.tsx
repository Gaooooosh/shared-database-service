import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from 'antd'
import AppLayout from './components/Layout/AppLayout'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import RecordsPage from './pages/RecordsPage'
import FilesPage from './pages/FilesPage'
import PermissionsPage from './pages/PermissionsPage'
import TestReportPage from './pages/TestReportPage'
import { useAuthStore } from './store/authStore'

function App() {
  const { token } = useAuthStore()

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Routes>
        <Route
          path="/login"
          element={token ? <Navigate to="/" replace /> : <LoginPage />}
        />
        <Route
          path="/"
          element={
            token ? (
              <AppLayout />
            ) : (
              <Navigate to="/login" replace />
            )
          }
        >
          <Route index element={<DashboardPage />} />
          <Route path="records" element={<RecordsPage />} />
          <Route path="files" element={<FilesPage />} />
          <Route path="permissions" element={<PermissionsPage />} />
          <Route path="test-report" element={<TestReportPage />} />
        </Route>
      </Routes>
    </Layout>
  )
}

export default App
