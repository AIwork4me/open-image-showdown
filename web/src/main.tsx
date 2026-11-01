import React from 'react';
import ReactDOM from 'react-dom/client';
import { createHashRouter, RouterProvider } from 'react-router-dom';
import './styles/global.css';
import Home from './pages/Home';
import CaseDetail from './pages/CaseDetail';
import Contribute from './pages/Contribute';
import Methodology from './pages/Methodology';
import Layout from './components/Layout';

const router = createHashRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      { index: true, element: <Home /> },
      { path: 'case/:caseId', element: <CaseDetail /> },
      { path: 'contribute', element: <Contribute /> },
      { path: 'methodology', element: <Methodology /> },
      { path: '*', element: <Home /> },
    ],
  },
]);

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>
);
