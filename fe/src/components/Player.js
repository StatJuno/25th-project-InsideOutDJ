// src/components/Player.js
import React from "react";

function Player({
  togglePlayPause,
  skipToNext,
  skipToPrevious,
  setVolume,
  playlists,
  playPlaylist,
  pliName,
}) {
  return (
    <div>
      <h1>플레이리스트: {pliName}</h1>
      <div>
        <button onClick={togglePlayPause}>재생/일시 중지</button>
        <button onClick={skipToNext}>다음 트랙</button>
        <button onClick={skipToPrevious}>이전 트랙</button>
        <input
          type="range"
          min="0"
          max="1"
          step="0.01"
          onChange={(e) => setVolume(e.target.value)}
        />
        {playlists.map((track) => (
          <div key={track.track.id}>{track.track.name}</div>
        ))}
      </div>
    </div>
  );
}

export default Player;
