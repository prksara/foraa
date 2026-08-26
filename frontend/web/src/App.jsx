import { BrowserRouter, Routes, Route } from "react-router-dom";
import "./App.css";
import Layout from "./components/Layout";

import Home from "./pages/Home";
import Assistant from "./pages/Assistant";
import MyHealth from "./pages/MyHealth";
import Reports from "./pages/Reports";
import Nutrition from "./pages/Nutrition";
import Wellness from "./pages/Wellness";
import Settings from "./pages/Settings";

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/assistant" element={<Assistant />} />
          <Route path="/health" element={<MyHealth />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/nutrition" element={<Nutrition />} />
          <Route path="/wellness" element={<Wellness />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;