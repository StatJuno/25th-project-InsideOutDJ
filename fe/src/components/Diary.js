// src/components/Diary.js
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

function Diary({ onCreatePlaylist }) {
  const [diary, setDiary] = useState("");
  const navigate = useNavigate();

  const handleDiarySubmit = async () => {
    await onCreatePlaylist(diary);
    navigate("/loading");
  };

  return (
    <div>
      <h1>오늘의 일기</h1>
      <textarea
        value={diary}
        onChange={(e) => setDiary(e.target.value)}
        placeholder="일기를 작성하세요..."
      />
      <button onClick={handleDiarySubmit}>플레이리스트 생성</button>
    </div>
  );
}

export default Diary;
