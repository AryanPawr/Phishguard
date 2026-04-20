import { useEffect, useState } from "react";
import shield from "./assets/phishguard-shield.svg";
import Dashboard from "./pages/Dashboard.jsx";
import Login from "./pages/Login.jsx";
import { clearToken, getToken } from "./services/api.js";

export default function App() {
  const [token, setToken] = useState(getToken());

  useEffect(() => {
    setToken(getToken());
  }, []);

  if (!token) {
    return <Login onLogin={() => setToken(getToken())} shield={shield} />;
  }

  return (
    <Dashboard
      shield={shield}
      onLogout={() => {
        clearToken();
        setToken(null);
      }}
    />
  );
}

