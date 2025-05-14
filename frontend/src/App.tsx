// src/App.tsx
import React, { Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Outlet } from 'react-router-dom';
import { Spinner, Container } from 'react-bootstrap';

import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';

import ProtectedRoute from './components/common/ProtectedRoute';
import GlobalErrorToast from './components/common/ErrorToast';
import NavigationBar from './components/layout/NavigationBar';
import { Link } from 'react-router-dom';

// Lazy load pages for better initial load time
const LoginPage = React.lazy(() => import('./pages/LoginPage'));
const LogoutPage = React.lazy(() => import('./pages/LogoutPage'));
const HomePage = React.lazy(() => import('./pages/HomePage'));
const FoldersPage = React.lazy(() => import('./pages/FoldersPage'));
const PeoplePage = React.lazy(() => import('./pages/PeoplePage'));
const ProfilePage = React.lazy(() => import('./pages/ProfilePage'));
const SettingsPage = React.lazy(() => import('./pages/SettingsPage'));
const FolderDetail = React.lazy(() => import('./pages/FolderDetail'));
const ImageDetail = React.lazy(() => import('./pages/ImageDetail'));
const PersonDetailsPage = React.lazy(() => import('./pages/PersonDetailsPage'));
const AlbumsPage = React.lazy(() => import('./pages/AlbumsPage'));

const AppLayout: React.FC = () => {
  return (
    <>
      <NavigationBar />
      <main>
        <Suspense fallback={
          <Container fluid className="d-flex justify-content-center align-items-center" style={{ height: 'calc(100vh - 56px)' }}> {/* Adjust height based on navbar */}
            <Spinner animation="border" role="status">
              <span className="visually-hidden">Loading page...</span>
            </Spinner>
          </Container>
        }>
          <Outlet /> {/* Nested routes will render here */}
        </Suspense>
      </main>
      <GlobalErrorToast />
    </>
  );
};


function App(): React.JSX.Element {
  return (
    <ThemeProvider>
      <Router>
        <AuthProvider> {/* AuthProvider wraps routes that need auth state */}
          <Routes>
            <Route path="/login" element={
              <Suspense fallback={<Spinner animation="border" />}>
                <LoginPage />
              </Suspense>
            } />
            <Route path="/logout" element={
              <Suspense fallback={<Spinner animation="border" />}>
                <LogoutPage />
              </Suspense>
            } />

            {/* Routes requiring authentication and the main layout */}
            <Route element={<AppLayout />}> {/* Layout component wraps protected routes */}
              <Route element={<ProtectedRoute />}> {/* Protects all child routes */}
                <Route path="/" element={<HomePage />} />
                <Route path="/folders" element={<FoldersPage />} />
                <Route path="/folders/:id" element={<FolderDetail />} />
                <Route path="/people" element={<PeoplePage />} />
                <Route path="/profile" element={<ProfilePage />} />
                <Route path="/images/:id" element={<ImageDetail />} />
                <Route path="/settings" element={<SettingsPage />} />
                <Route path='/people/:id' element={<PersonDetailsPage/>}/>
                <Route path='/albums/' element={<AlbumsPage/>}/>
                {/* Add other protected routes here */}
              </Route>
            </Route>

            {/* Catch-all for 404 - Not Found (Optional) */}
            <Route path="*" element={
              <Container className="text-center p-5">
                <h1>404 - Not Found</h1>
                <p>The page you are looking for does not exist.</p>
                <Link to="/">Go to Homepage</Link>
              </Container>
            } />
          </Routes>
        </AuthProvider>
      </Router>
    </ThemeProvider>
  );
}

export default App;
