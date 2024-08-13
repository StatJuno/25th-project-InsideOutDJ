// src/components/Login.js
import React from "react";
import { useNavigate } from "react-router-dom";

function Login({ authEndpoint, clientId, redirectUri, scope, token, logout }) {
  const navigate = useNavigate();
  // 로그인 성공 후 일기 화면으로 이동
  const handleLogin = () => {
    if (token) {
      navigate("/diary");
    }
  };
  return (
    <div>
      <h1>Spotify 로그인</h1>
      {!token ? (
        <a
          href={`${authEndpoint}?client_id=${clientId}&redirect_uri=${redirectUri}&response_type=token&scope=${scope}`}
        >
          스포티파이에 로그인하세요
        </a>
      ) : (
        <button
          onClick={() => {
            logout();
            navigate("/");
          }}
        >
          로그아웃
        </button>
      )}
      <button onClick={handleLogin}>go</button>
    </div>
  );
}

export default Login;
