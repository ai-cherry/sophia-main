import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import DashboardLayout from './components/dashboard/DashboardLayout'
import './App.css'

function App() {
  // Set dark theme by default
  useEffect(() => {
    document.documentElement.classList.add('dark');
  }, []);

  return (
    <Router>
      <Routes>
        <Route path="/" element={<DashboardLayout />} />
        <Route path="/dashboard" element={<DashboardLayout />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  )
}

export default App

