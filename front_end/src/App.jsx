import { BrowserRouter } from 'react-router-dom';

import { AuthProvider } from './context/AuthContext';
import { ConfirmProvider } from './components/ConfirmDialog';
import AppRoutes from './routes';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ConfirmProvider>
          <AppRoutes />
        </ConfirmProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
