import { lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import ErrorBoundary from "./components/ErrorBoundary";

const DashboardPage = lazy(() => import("./pages/DashboardPage"));
const AboutPage = lazy(() => import("./pages/AboutPage"));   // <-- new

function LoadingFallback() {
  return (
    <div className="min-h-screen flex items-center justify-center text-gray-500">
      Loading...
    </div>
  );
}
function AppRoutes() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/about" element={<AboutPage />} />   {/* <-- new */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </ErrorBoundary>
  );
}