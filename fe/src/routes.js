// src/routes.js

import React from "react";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";

import Diary from "./components/Diary";
import Login from "./components/Login";
import Loading from "./components/Loading";
import Player from "./components/Player";

function AppRoutes({ playerProps, authProps }) {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login {...authProps} />} />
        <Route
          path="/diary"
          element={<Diary onCreatePlaylist={playerProps.onCreatePlaylist} />}
        />
        <Route path="/loading" element={<Loading />} />
        <Route path="/player" element={<Player {...playerProps} />} />
      </Routes>
    </Router>
  );
}

export default AppRoutes;
