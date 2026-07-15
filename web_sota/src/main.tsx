import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Layout } from "./Layout";
import { Dashboard } from "./pages/Dashboard";
import { Personas } from "./pages/Personas";
import { Chat } from "./pages/Chat";
import { Safety } from "./pages/Safety";
import { Audit } from "./pages/Audit";
import { Compliance } from "./pages/Compliance";
import { Help } from "./pages/Help";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/personas" element={<Personas />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/safety" element={<Safety />} />
          <Route path="/audit" element={<Audit />} />
          <Route path="/compliance" element={<Compliance />} />
          <Route path="/help" element={<Help />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  </React.StrictMode>
);
