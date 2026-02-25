import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import ReportPage from './pages/ReportPage'
import DemoPage from './pages/DemoPage'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/report" element={<ReportPage />} />
        <Route path="/demo" element={<DemoPage />} />
      </Route>
    </Routes>
  )
}
