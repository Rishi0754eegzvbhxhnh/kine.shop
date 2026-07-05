import { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import ProductPanel from './components/ProductPanel'
import ShoppableVideoPlayer from './components/ShoppableVideoPlayer'
import VideoCarousel from './components/VideoCarousel'

const DUMMY_VIDEOS = [
  { title: "Neon Dreams", category: "Sci-Fi", tags: ["Cyberpunk", "Action"], bgGradient: "from-purple-900 to-indigo-900", file: "/Charade_1963_short.mp4" },
  { title: "Charade (1963)", category: "Classic", tags: ["Romance", "Mystery"], bgGradient: "from-gray-800 to-black", file: "/Charade_1963.mp4" },
  { title: "Echoes of Time", category: "Drama", tags: ["Emotional", "Time Travel"], bgGradient: "from-blue-900 to-cyan-900", file: "/Charade_1963_short.mp4" },
  { title: "Midnight Pursuit", category: "Action", tags: ["Thriller", "Heist"], bgGradient: "from-red-900 to-black", file: "/Charade_1963_short.mp4" },
  { title: "Solar Winds", category: "Sci-Fi", tags: ["Space", "Adventure"], bgGradient: "from-orange-900 to-red-900", file: "/Charade_1963_short.mp4" },
  { title: "The Last Stand", category: "Action", tags: ["Survival", "Gritty"], bgGradient: "from-green-900 to-emerald-900", file: "/Charade_1963_short.mp4" },
  { title: "Digital Shadows", category: "Thriller", tags: ["Hacking", "Mystery"], bgGradient: "from-teal-900 to-slate-900", file: "/Charade_1963_short.mp4" }
];

function App() {
  const [selectedVideo, setSelectedVideo] = useState(null)
  const [metadata, setMetadata] = useState(null)
  const [isProcessing, setIsProcessing] = useState(false)
  
  const [selectedProduct, setSelectedProduct] = useState(null)
  const [isLoadingProduct, setIsLoadingProduct] = useState(false)
  const fileInputRef = useRef(null)

  // Automatically trigger AI detection when a video is selected
  useEffect(() => {
    if (selectedVideo && !metadata && !isProcessing) {
      handleAnalyzeVideo();
    }
  }, [selectedVideo]);

  const handleWatchNow = async () => {
    setSelectedVideo('/Charade_1963_short.mp4')
    setMetadata(null)
    setSelectedProduct(null)
    
    // Fetch local SAM3 inference results
    try {
      const response = await axios.get('/sam3_charade_timeline.json?t=' + new Date().getTime())
      if (response.data) {
        setMetadata({ timeline: response.data })
      }
    } catch (err) {
      console.error("Error fetching SAM3 metadata:", err);
    }
  }

  const handleAnalyzeVideo = async () => {
    if (!selectedVideo) return;
    
    setIsProcessing(true)
    try {
      if (typeof selectedVideo === 'string') {
        // Dummy data was selected, fetch existing metadata by filename
        const filename = selectedVideo.split('/').pop();
        const response = await axios.get(`http://${window.location.hostname}:8082/api/video-metadata/by-filename?name=${filename}`);
        if (response.data && response.data.timeline) {
          setMetadata(response.data)
        } else {
          alert("Metadata not found in database. The AI analysis script might still be running!");
        }
      } else {
        // User uploaded a local File object
        const formData = new FormData()
        formData.append('file', selectedVideo)
        const response = await axios.post(`http://${window.location.hostname}:8082/api/video-metadata/upload`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        if (response.data && response.data.timeline) {
          setMetadata(response.data)
        } else {
          alert("Failed to analyze video properly.");
        }
      }
    } catch (err) {
      console.error("Error analyzing video:", err)
      alert("Failed to analyze video. Ensure Spring Boot and Docker are running.")
    } finally {
      setIsProcessing(false)
    }
  }

  const handleBoxClick = async (boxData, videoElement) => {

    setIsLoadingProduct(true)
    try {
      const response = await axios.get(`http://${window.location.hostname}:8082/api/products/search?query=${boxData.product}`)
      setSelectedProduct({
        ...response.data,
        label: boxData.product,
        price: boxData.price,
        category: boxData.category,
        shopUrl: boxData.shop_url,
        twelvelabs_analysis: metadata?.twelvelabs_analysis
      })
    } catch (err) {
      console.error("Error fetching product:", err)
      setSelectedProduct({
        label: boxData.product,
        price: boxData.price,
        category: boxData.category,
        shopUrl: boxData.shop_url,
        twelvelabs_analysis: metadata?.twelvelabs_analysis
      })
    } finally {
      setIsLoadingProduct(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col bg-[#09090b] text-[#f9fafb] font-sans relative overflow-hidden transition-all duration-500">
      
      {/* Top Navigation Bar */}
      <header className="flex items-center justify-between px-8 py-4 bg-[#030303] border-b border-white/5 sticky top-0 z-30">
        <div className="flex items-center gap-12">
          <div className="text-2xl font-bold font-ubuntu tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-pink-500 cursor-pointer">
            kine.shop
          </div>
          <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-gray-400">
            <a href="#" className="hover:text-white transition-colors">Home</a>
            <a href="#" className="hover:text-cyan-400 transition-colors text-white">Browse</a>
            <a href="#" className="hover:text-white transition-colors">Anime</a>
            <a href="#" className="hover:text-white transition-colors">Food</a>
            <a href="#" className="hover:text-white transition-colors">Cinema</a>
          </nav>
        </div>
        <div className="flex items-center gap-4">
          <div className="relative">
            <input 
              type="text" 
              placeholder="Search movies, products, brands..." 
              className="bg-transparent border border-white/10 rounded-full px-4 py-2 text-sm w-64 focus:outline-none focus:border-cyan-500 transition-colors text-white placeholder-[#9ca3af]"
            />
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className={`flex-grow flex flex-col items-center pt-8 pb-20 px-6 transition-all duration-500 ${selectedProduct ? 'mr-[400px]' : ''}`}>
        
        {/* If no video is selected, show the Hero / Upload section */}
        {!selectedVideo && (
          <div className="w-full flex flex-col items-center">
            
            {/* Hero Section */}
            <div className="relative w-full overflow-hidden mb-12 group h-[70vh]">
              <div className="absolute inset-0 bg-gradient-to-r from-black via-black/50 to-transparent z-10 pointer-events-none" />
              <div className="absolute inset-0 bg-gradient-to-t from-[#09090b] via-transparent to-transparent z-10 pointer-events-none" />
              {/* Hero Background image (Vertical Poster fitted to the right) */}
              <div 
                className="w-full h-full opacity-80 absolute inset-0 z-0 bg-right bg-no-repeat bg-contain md:bg-[auto_120%]"
                style={{ backgroundImage: 'url(/CHARADE_poster.jpg)' }}
              />
              
              <div className="absolute top-0 left-0 h-full flex flex-col justify-center px-16 z-20 w-full md:w-1/2">
                <h1 className="text-6xl md:text-7xl font-black mb-4 tracking-tight text-white drop-shadow-2xl">
                  Charade
                </h1>
                <div className="flex gap-4 text-sm font-bold text-gray-300 mb-6 drop-shadow-lg">
                  <span className="text-green-500">98% Match</span>
                  <span>1963</span>
                  <span className="border border-gray-500 px-1">PG</span>
                  <span>1h 53m</span>
                </div>
                <p className="text-white mb-8 text-lg max-w-xl leading-relaxed font-medium drop-shadow-lg">
                  Romance and suspense blend in Paris as a widow is pursued by several men who want a fortune her murdered husband had stolen. Whom can she trust?
                </p>
                
                <div className="flex items-center gap-4">
                  <button 
                    onClick={() => {
                      setSelectedVideo('/Charade_1963_short.mp4')
                      setMetadata(null)
                      setSelectedProduct(null)
                    }}
                    className="px-8 py-3 rounded text-lg font-bold text-black bg-white hover:bg-gray-200 transition-colors flex items-center gap-2"
                  >
                    <span className="text-2xl leading-none">▶</span> Play
                  </button>
                  <button className="px-8 py-3 rounded text-lg font-bold text-white bg-gray-500/50 hover:bg-gray-500/70 transition-colors flex items-center gap-2">
                    <span className="text-2xl leading-none">ℹ</span> More Info
                  </button>
                </div>
              </div>
            </div>

            {/* Netflix Style Carousels */}
            <div className="w-full -mt-32 z-20 relative">
              <VideoCarousel 
                title="Trending Now" 
                videos={DUMMY_VIDEOS.slice(0, 5)} 
                onPlay={(v) => { setSelectedVideo(v.file); setMetadata(null); setSelectedProduct(null); }} 
              />
              <VideoCarousel 
                title="Shoppable Picks For You" 
                videos={DUMMY_VIDEOS.slice(2, 7)} 
                onPlay={(v) => { setSelectedVideo(v.file); setMetadata(null); setSelectedProduct(null); }} 
              />
              <VideoCarousel 
                title="Action Thrillers" 
                videos={[...DUMMY_VIDEOS].reverse()} 
                onPlay={(v) => { setSelectedVideo(v.file); setMetadata(null); setSelectedProduct(null); }} 
              />
            </div>
          </div>
        )}

        {/* Video Player Section */}
        {selectedVideo && (
          <div className="w-full max-w-6xl flex flex-col">
            <div className="mb-6 flex justify-between items-center">
              <h2 className="text-2xl font-bold font-ubuntu tracking-wide flex items-center gap-3">
                <span className="w-2 h-2 rounded-full bg-cyan-400 box-glow" />
                Live Stream Analysis
              </h2>
              <div className="flex gap-4">
                <button 
                  onClick={() => {
                    setSelectedVideo(null)
                    setMetadata(null)
                  }}
                  className="text-sm text-gray-400 hover:text-white transition-colors"
                >
                  ← Back to Browse
                </button>
                {!metadata && (
                  <button 
                    onClick={handleAnalyzeVideo} 
                    disabled={isProcessing}
                    className={`px-6 py-2 rounded-full font-bold text-white transition-all text-sm ${isProcessing ? 'bg-gray-700 cursor-not-allowed' : 'bg-cyan-600 hover:bg-cyan-500 box-glow shadow-cyan-500/30'}`}
                  >
                    {isProcessing ? 'Analyzing AI Stream...' : 'Initialize AI Detection'}
                  </button>
                )}
              </div>
            </div>

            <div className="w-full bg-[#0a0a0c] border border-[#222] rounded-xl p-2 shadow-2xl">
              <ShoppableVideoPlayer 
                videoFile={selectedVideo} 
                metadata={metadata} 
                onBoxClick={handleBoxClick} 
              />
            </div>
          </div>
        )}
      </main>

      {/* Loading overlay for product */}
      {isLoadingProduct && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 flex flex-col items-center justify-center">
          <div className="w-16 h-16 border-4 border-cyan-500/30 border-t-cyan-400 rounded-full animate-spin mb-4" />
          <div className="text-cyan-400 font-ubuntu font-bold tracking-widest uppercase text-glow">
            Scanning Neural Net for Product...
          </div>
        </div>
      )}

      {/* Product Panel side drawer */}
      <ProductPanel product={selectedProduct} onClose={() => setSelectedProduct(null)} />
    </div>
  )
}

export default App
