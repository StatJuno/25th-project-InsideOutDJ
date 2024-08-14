import React, { useEffect, useState } from "react";
import AppRoutes from "./routes";
import axios from "axios"; // axios를 사용하려면 임포트 추가

function App() {
  const CLIENT_ID = "072d48a69d3247b0a03ac8c3734997b2";
  const REDIRECT_URI = "http://localhost:3000/";
  const AUTH_ENDPOINT = "https://accounts.spotify.com/authorize";
  const SCOPE = [
    "playlist-modify-public",
    "playlist-modify-private",
    "user-modify-playback-state",
    "user-read-playback-state",
    "user-read-currently-playing",
    "streaming",
  ].join(" ");

  const [token, setToken] = useState("");
  const [deviceId, setDeviceId] = useState(null);
  const [player, setPlayer] = useState(null);
  const [pliKey, setPliKey] = useState("");
  const [pliName, setPliName] = useState("");
  const [playlists, setPlaylists] = useState([]);
  const [isPlaying, setIsPlaying] = useState(false);

  // useEffect 내부에서 상태를 사용
  useEffect(() => {
    const hash = window.location.hash;
    let token = window.localStorage.getItem("token");

    if (!token && hash) {
      token = hash
        .substring(1)
        .split("&")
        .find((elem) => elem.startsWith("access_token"))
        .split("=")[1];
      window.location.hash = "";
      window.localStorage.setItem("token", token);
    }
    setToken(token);

    if (token) {
      window.onSpotifyWebPlaybackSDKReady = () => {
        const player = new window.Spotify.Player({
          name: "Web Playback SDK Player",
          getOAuthToken: (cb) => {
            cb(token);
          },
          volume: 0.5,
        });

        player.addListener("ready", ({ device_id }) => {
          console.log("Ready with Device ID", device_id);
          setDeviceId(device_id);
          transferPlaybackToDevice(device_id);
        });

        player.addListener("not_ready", ({ device_id }) => {
          console.log("Device ID has gone offline", device_id);
        });

        player.addListener("player_state_changed", (state) => {
          console.log(state);
        });

        player.connect();
        setPlayer(player);
      };
    }
  }, [token]);

  const transferPlaybackToDevice = async (deviceId) => {
    try {
      await axios.put(
        "https://api.spotify.com/v1/me/player",
        {
          device_ids: [deviceId],
          play: true,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      );
      console.log("Playback transferred to device:", deviceId);
    } catch (error) {
      console.error("Playback transfer failed:", error);
      alert("Playback transfer failed. Please try again.");
    }
  };

  // authProps 및 playerProps를 필요에 따라 전달
  const authProps = {
    authEndpoint: AUTH_ENDPOINT,
    clientId: CLIENT_ID,
    redirectUri: REDIRECT_URI,
    scope: SCOPE,
    logout: () => {
      setToken("");
      window.localStorage.removeItem("token");
    },
    token: token,
  };
  const playerProps = {
    player,
    isPlaying,
    togglePlayPause: async () => {
      if (!player) return;
      const state = await player.getCurrentState();
      if (!state) {
        console.error("플레이어 상태를 가져올 수 없습니다.");
        return;
      }

      if (state.paused) {
        player.resume().then(() => {
          console.log("음악이 재생되었습니다.");
          setIsPlaying(true);
        });
      } else {
        player.pause().then(() => {
          console.log("음악이 일시 중지되었습니다.");
          setIsPlaying(false);
        });
      }
    },
    skipToNext: () => {
      if (!player) return;
      player.nextTrack().then(() => {
        console.log("다음 트랙으로 이동했습니다.");
      });
    },
    skipToPrevious: () => {
      if (!player) return;
      player.previousTrack().then(() => {
        console.log("이전 트랙으로 이동했습니다.");
      });
    },

    setVolume: (volume) => {
      if (!player) return;
      player.setVolume(volume).then(() => {
        console.log(`볼륨이 ${volume * 100}%로 설정되었습니다.`);
      });
    },
    playlists,
    playPlaylist: async (playlistUri) => {
      console.log("Attempting to play playlist with URI:", playlistUri);
      console.log("Using device ID:", deviceId);

      if (!deviceId) {
        alert("플레이어가 준비되지 않았습니다. 잠시 후 다시 시도하세요.");
        return;
      }

      try {
        await axios.put(
          "https://api.spotify.com/v1/me/player/play",
          {
            context_uri: playlistUri,
            device_id: deviceId,
          },
          {
            headers: {
              Authorization: `Bearer ${token}`,
              "Content-Type": "application/json",
            },
          }
        );
        alert("플레이리스트가 재생되었습니다.");
      } catch (error) {
        console.error("플레이리스트 재생 중 오류 발생:", error);
        console.log("Response:", error.response);
        alert("플레이리스트 재생 중 오류가 발생했습니다.");
      }
    },
    pliName,
    onCreatePlaylist: async (diary) => {
      const playlistName = `Diary Playlist - ${new Date().toLocaleDateString()}`;
      try {
        const userResponse = await axios.get("https://api.spotify.com/v1/me", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        const userId = userResponse.data.id;

        const playlistResponse = await axios.post(
          `https://api.spotify.com/v1/users/${userId}/playlists`,
          {
            name: playlistName,
            description: "Playlist created based on diary entry",
            public: false,
          },
          {
            headers: {
              Authorization: `Bearer ${token}`,
              "Content-Type": "application/json",
            },
          }
        );

        setPliKey(playlistResponse.data.id);
        setPliName(playlistResponse.data.name);

        // 감정 분석 후 트랙 추가 로직 추가
        let uri_base = "spotify:track:";
        let uris = ["2rOA9vEsnpNB6L5XgmibKn", "3PGK6qlEztoGlpJoW603YA"].map(
          (i) => `${uri_base}${i}`
        );

        await axios.post(
          `https://api.spotify.com/v1/playlists/${playlistResponse.data.id}/tracks`,
          {
            uris: uris,
            position: 0,
          },
          {
            headers: {
              Authorization: `Bearer ${token}`,
              "Content-Type": "application/json",
            },
          }
        );

        alert("플레이리스트가 생성되고 트랙이 추가되었습니다.");
      } catch (error) {
        console.error("플레이리스트 생성 중 오류 발생:", error);
        alert("플레이리스트 생성 중 오류가 발생했습니다.");
      }
    },
  };
  return <AppRoutes playerProps={playerProps} authProps={authProps} />;
}

export default App;
