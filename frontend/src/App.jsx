import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import AnomalyExplorer from './pages/AnomalyExplorer'
import Methodology from './pages/Methodology'

export default function App() {
  return (
    <div className="min-h-screen bg-[#0f1117] text-gray-100">
      <Navbar />
      <main>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/anomalies" element={<AnomalyExplorer />} />
          <Route path="/methodology" element={<Methodology />} />
        </Routes>
      </main>
      <footer className="border-t border-[#2e3347] mt-12 py-6 text-center text-xs text-gray-500">
        SmartWatt India · Statistics for Machine Learning &amp; Data Science ·{' '}
        Dataset:{' '}
        <a
          href="https://doi.org/10.7910/DVN/7MEXN4"
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-400 hover:underline"
        >
          IIIT-Delhi doi:10.7910/DVN/7MEXN4
        </a>
      </footer>
    </div>
  )
}
