import React from 'react'
import ReactDOM from 'react-dom/client'
import WindowsApp from './windows/App'
import './windows/styles.css'

const isMac = navigator.platform.toLowerCase().includes('mac')
const App = React.lazy(() => isMac ? import('./mac/App') : Promise.resolve({ default: WindowsApp }))

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode><React.Suspense fallback={null}><App /></React.Suspense></React.StrictMode>,
)
