import React, { useState, useRef, useEffect, useCallback } from 'react';

const ShoppableVideoPlayer = ({ videoFile, metadata, onBoxClick }) => {
  const [currentTime, setCurrentTime] = useState(0);
  const [currentDetections, setCurrentDetections] = useState([]);
  const [renderRect, setRenderRect] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const videoRef = useRef(null);

  // Robustly compute the actual rendered video content area inside the element
  // Uses requestAnimationFrame to wait until browser has painted the element
  const [isPlaying, setIsPlaying] = useState(false);
  const [duration, setDuration] = useState(0);

  // Robustly compute the actual rendered video content area inside the element
  // Uses requestAnimationFrame to wait until browser has painted the element
  const computeRenderRect = useCallback(() => {
    requestAnimationFrame(() => {
      const video = videoRef.current;
      if (!video || !video.videoWidth || !video.videoHeight) return;

      const displayW = video.clientWidth;
      const displayH = video.clientHeight;
      const nativeW = video.videoWidth;
      const nativeH = video.videoHeight;

      if (!displayW || !displayH) return;

      // Match what object-contain does: scale uniformly to fit, centered
      const scale = Math.min(displayW / nativeW, displayH / nativeH);
      const renderedW = nativeW * scale;
      const renderedH = nativeH * scale;
      const offsetX = (displayW - renderedW) / 2;
      const offsetY = (displayH - renderedH) / 2;

      setRenderRect({ offsetX, offsetY, renderedW, renderedH, nativeW, nativeH });
    });
  }, []);

  // Use ResizeObserver for reliable re-computation on any size change
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    const observer = new ResizeObserver(computeRenderRect);
    observer.observe(video);
    return () => observer.disconnect();
  }, [computeRenderRect]);

  const handleTimeUpdate = () => {
    if (videoRef.current) setCurrentTime(videoRef.current.currentTime);
  };

  const handleLoadedMetadata = () => {
    if (videoRef.current) setDuration(videoRef.current.duration);
    computeRenderRect();
  };

  const togglePlay = () => {
    if (videoRef.current) {
      if (videoRef.current.paused) {
        videoRef.current.play();
        setIsPlaying(true);
      } else {
        videoRef.current.pause();
        setIsPlaying(false);
      }
    }
  };

  const formatTime = (timeInSeconds) => {
    const m = Math.floor(timeInSeconds / 60);
    const s = Math.floor(timeInSeconds % 60);
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  const videoUrl = React.useMemo(() => {
    if (!videoFile) return null;
    if (typeof videoFile === 'string') return videoFile;
    return URL.createObjectURL(videoFile);
  }, [videoFile]);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    
    setIsSearching(true);
    try {
      const res = await fetch(`http://${window.location.hostname}:8082/api/video-metadata/search?query=${encodeURIComponent(searchQuery)}`);
      const data = await res.json();
      
      if (data.data && data.data.length > 0) {
        const bestMatch = data.data[0];
        if (videoRef.current) {
          videoRef.current.currentTime = bestMatch.start;
          videoRef.current.play();
          setIsPlaying(true);
        }
      } else {
        alert("No semantic match found!");
      }
    } catch (error) {
      console.error("Semantic Search Error:", error);
    } finally {
      setIsSearching(false);
    }
  };

  const currentBoxes = React.useMemo(() => {
    if (!metadata || !metadata.timeline) return [];
    // Convert current time to frame index (assuming 24 FPS)
    const frame = Math.floor(currentTime * 24);
    return metadata.timeline[String(frame)] || [];
  }, [metadata, currentTime]);

  const [showAnalysis, setShowAnalysis] = useState(false);

  const uniqueObjects = React.useMemo(() => {
    if (!metadata || !metadata.timeline) return [];
    const uniqueMap = new Map();
    Object.values(metadata.timeline).forEach(boxes => {
      boxes.forEach(box => {
        const key = box.label || box.product;
        if (!uniqueMap.has(key)) {
          uniqueMap.set(key, box);
        }
      });
    });
    return Array.from(uniqueMap.values());
  }, [metadata]);

  if (!videoUrl) return null;

  return (
    <div className="relative w-full rounded-xl overflow-hidden bg-[#030303] group shadow-2xl border border-white/5" style={{ display: 'inline-block' }}>
      <video
        ref={videoRef}
        src={videoUrl}
        controls={false}
        className="block max-w-full w-full cursor-pointer"
        style={{ maxHeight: '75vh', objectFit: 'contain', display: 'block' }}
        onClick={togglePlay}
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleLoadedMetadata}
      />

      {/* SVG Overlay for Pixel-Perfect SAM Masks */}
      {renderRect && (
        <svg 
          viewBox="0 0 100 100" 
          preserveAspectRatio="none" 
          className="absolute pointer-events-none" 
          style={{ 
            zIndex: 10,
            left: `${renderRect.offsetX}px`,
            top: `${renderRect.offsetY}px`,
            width: `${renderRect.renderedW}px`,
            height: `${renderRect.renderedH}px`
          }}
        >
        {currentBoxes.map((boxData, index) => {
          if (!boxData.mask) return null;
          
          const points = boxData.mask.map(pt => `${pt[0]},${pt[1]}`).join(' ');

          return (
            <g key={index} className="group/box pointer-events-auto cursor-pointer" onClick={(e) => {
              e.stopPropagation();
              if (navigator.vibrate) navigator.vibrate(50);
              if (onBoxClick) onBoxClick(boxData, videoRef.current);
            }}>
              <polygon
                points={points}
                className="fill-cyan-500/10 stroke-cyan-400 hover:fill-cyan-500/30 transition-all duration-300"
                style={{ strokeWidth: 0.3, vectorEffect: 'non-scaling-stroke', strokeDasharray: '2,2' }}
              />
              <text x={boxData.mask[0][0]} y={boxData.mask[0][1] > 2 ? boxData.mask[0][1] - 1 : boxData.mask[0][1] + 2} fontSize="2" className="opacity-0 group-hover/box:opacity-100 fill-white font-bold drop-shadow-md transition-opacity duration-300">
                {boxData.label || boxData.product}
              </text>
            </g>
          );
        })}
        </svg>
      )}
      {/* Custom Player Controls */}
      <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-[#030303]/95 to-transparent flex items-center justify-between z-20">
        <div className="flex items-center gap-4">
          <button onClick={togglePlay} className="text-white hover:text-cyan-400 transition-colors focus:outline-none">
            {isPlaying ? (
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24"><path d="M6 4h4v16H6zm8 0h4v16h-4z"/></svg>
            ) : (
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
            )}
          </button>
          <div className="text-xs font-semibold text-white/80 font-mono tracking-wider">
            {formatTime(currentTime)} / {formatTime(duration)}
          </div>
        </div>
        
        <div className="hidden md:flex items-center gap-4">
           <button onClick={() => { if(videoRef.current) { videoRef.current.currentTime -= 10; } }} className="text-white hover:text-cyan-400">⏪ 10s</button>
           <button onClick={() => { if(videoRef.current) { videoRef.current.currentTime += 10; } }} className="text-white hover:text-cyan-400">10s ⏩</button>
           
           <input type="range" min="0" max="1" step="0.1" defaultValue="1" 
             onChange={(e) => { if(videoRef.current) videoRef.current.volume = e.target.value; }}
             className="w-20 accent-cyan-400"
           />
           
           <button onClick={() => { if(videoRef.current) videoRef.current.requestFullscreen(); }} className="text-white hover:text-cyan-400 font-mono text-xs uppercase border border-white/20 px-2 py-1 rounded">
             Fullscreen
           </button>
           
           <span className="px-2 py-1 rounded-md bg-white/10 border border-white/5 text-[10px] text-white/70 font-mono uppercase tracking-widest">
             YOLOv8 Fast-Track
           </span>
        </div>

        <div className="flex items-center gap-3">
          <form onSubmit={handleSearch} className="relative hidden md:block">
            <input 
              type="text" 
              placeholder="Semantic Video Search..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-white/10 border border-white/20 text-white text-xs rounded-full px-4 py-1.5 focus:outline-none focus:border-cyan-400 w-64 transition-colors"
            />
            <button type="submit" className="absolute right-2 top-1/2 -translate-y-1/2 text-white/70 hover:text-cyan-400">
              {isSearching ? <span className="animate-spin text-xs">⏳</span> : <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>}
            </button>
          </form>

          <button 
            onClick={() => setShowAnalysis(!showAnalysis)}
            className={`flex items-center gap-1.5 border rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${showAnalysis ? 'bg-cyan-500/20 border-cyan-500 text-cyan-400' : 'bg-white/5 border-white/10 text-[#f9fafb] hover:bg-white/10'}`}
          >
            Analysis
          </button>
        </div>
      </div>

      {/* Analysis Overlay Panel */}
      {showAnalysis && (
        <div className="absolute top-4 right-4 bottom-20 w-80 bg-[#09090b]/95 backdrop-blur-xl border border-white/10 rounded-xl p-4 flex flex-col z-20 shadow-2xl overflow-hidden transition-all animate-fade-in">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-white font-bold tracking-wide flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-cyan-400 box-glow" />
              Detected Objects
            </h3>
            <button onClick={() => setShowAnalysis(false)} className="text-gray-400 hover:text-white">✕</button>
          </div>
          
          <div className="flex-1 overflow-y-auto space-y-3 pr-1 custom-scrollbar">
            {uniqueObjects.length > 0 ? uniqueObjects.map((obj, i) => (
              <div key={i} className="bg-white/5 border border-white/5 rounded-lg p-3 hover:bg-white/10 transition-colors group/item">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <h4 className="text-sm font-bold text-white capitalize">{obj.label || obj.product}</h4>
                    <span className="text-[10px] text-gray-400 uppercase tracking-wider">{obj.category || 'General'}</span>
                  </div>
                  <span className="text-cyan-400 font-mono text-sm">${obj.price || '59.99'}</span>
                </div>
                <div className="flex justify-between items-center mt-3">
                  <span className="text-xs text-gray-500 font-mono">Conf: {((obj.confidence || 0) * 100).toFixed(0)}%</span>
                  <a 
                    href={obj.shop_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-xs font-bold bg-white/10 hover:bg-cyan-500 hover:text-black px-3 py-1.5 rounded-full transition-all flex items-center gap-1 text-white"
                  >
                    Shop Now <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg>
                  </a>
                </div>
              </div>
            )) : (
              <div className="text-sm text-gray-400 text-center mt-10">No objects detected yet.</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ShoppableVideoPlayer;
