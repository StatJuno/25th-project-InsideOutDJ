// src/components/Loading.js
import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import tw from "tailwind-styled-components";

const Circle = tw.svg`
  animate-spin w-24 text-yellow 
`;

const OutBox = tw.div`
  flex items-center justify-center flex-col min-w-96 w-full  min-h-192 h-full
`;

const LoadingText = tw.h1`
  text-3xl animate-pulse m-6
`;

function LoadingCircle() {
  return (
    <Circle xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        stroke-width="4"
      ></circle>
      <path
        class="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      ></path>
    </Circle>
  );
}

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
    <OutBox>
      <LoadingText>기억저장소로 가는 중입니다....</LoadingText>
      <LoadingCircle></LoadingCircle>
    </OutBox>
  );
}

export default Loading;
