// src/components/Loading.js
import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";

function Loading({ onPlaylistReady }) {
  const navigate = useNavigate();

  useEffect(() => {
    const timeout = setTimeout(() => {
      // onPlaylistReady();
      navigate("/player");
    }, 3000); // 로딩 후 3초 뒤에 플레이어 화면으로 이동

    return () => clearTimeout(timeout);
  }, [navigate, onPlaylistReady]);

  return (
    <div>
      <h1>플레이리스트를 생성하는 중입니다...</h1>
    </div>
  );
}

export default Loading;
