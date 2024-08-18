import React, { useEffect, useState, useRef } from "react";
import tw from "tailwind-styled-components";

const SeekSlider = ({ progress, duration, seekTo}) => {
    const fullWidth = useRef(null);
    // Calculate the width percentage
    const [sliderWidth, setSliderWidth] = useState(0);
    const width = sliderWidth < 9? 0: sliderWidth > 8 && sliderWidth < 13? 13: sliderWidth;
    const thumbPos = sliderWidth;

    useEffect(() => {
        if (fullWidth.current) {
            setSliderWidth((progress / duration) * fullWidth.current.offsetWidth);
        }
    }, [progress, duration]);
  
    return (
        <div className="relative w-full">
           <input class="w-full h-3 accent-teal-400
                        bg-gray-200 rounded-lg opacity-0
                        cursor-pointer appearance-none"
                        type="range"
                        min="0"
                        max={duration}
                        step="1"
                        value={progress}
                        onChange={(e) => {
                          seekTo(e.target.value);
                        }}
                      />
            <div 
                className="absolute h-3.5 top-0 left-0 bg-teal-400 rounded-full mt-1 -mr-0 z-30"
                style={{ width: width, pointerEvents: 'none'}}
            ></div>
            <div ref={fullWidth}
                className="absolute h-3.5 w-full bg-gray-200 rounded-full -mt-5 z-20"
                style={{ pointerEvents: 'none'}}
            ></div>
            <svg 
                className="absolute mt-[-22px] z-40 w-[20px] h-[20px] cursor-pointer -translate-x-[50%]"
                style={{left: thumbPos, pointerEvents: "none"}}>
                    <circle cx="10" cy="10" r="8" stroke="#2dd4bf" stroke-width="3.6" fill="#FFF"/>
            </svg>
            {/* <div style={{left: thumbPos, pointerEvents: "none"}}>
                className="absolute" >
                
                {/* <div 
                    className="absolute w-5 h-5 -top-[23px] bg-teal-400 rounded-full z-30"
                ></div>
                <div 
                    className="absolute w-3 h-3 -top-[23px] left-1 bg-white rounded-full mt-1 z-40"
                ></div>
                
            </div> */}
        </div>
    );
  };
  
  export default SeekSlider