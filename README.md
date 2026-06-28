# 🎬 Shoppable-Streaming Platform — Microservices

⭐ If this project is helpful to you, please star this repo.
## 📌 What I Built
A complete **Shoppable-Streaming Platform** from scratch — production level code engineered to merge entertainment and e-commerce, giving users a seamless, tactile (haptic) feel to both watch and shop simultaneously.
You upload a video → FFmpeg encodes to 4 qualities automatically
                   → HLS chunks stored on AWS S3
                   → Streaming Service generates secure signed URLs
                   → Custom HLS Player streams the video

## 🏗️ Architecture
Admin adds movie → Content Service → MySQL

Admin uploads video → Video Service → AWS S3
                                         ↓
                              Kafka (video.uploaded)
                                         ↓
                              Encoding Service
                                         ↓
                    FFmpeg → 1080p, 720p, 480p, 360p HLS chunks
                                         ↓
                              Upload encoded files → AWS S3
                                         ↓
                              Kafka (video.encoded)
                                         ↓
                    ┌──────────────────────────────────┐
                    │                                  │
             Content Service                  Streaming Service
          updates HLS URL in MySQL          stores playlist key in Redis
                                                     ↓
User clicks play → Streaming Service → signs every HLS segment
                                     → returns signed master.m3u8
                                     → Custom player streams video ✅

## 🛠️ Services Overview

| Service | Port | Responsibility |
|---------|------|----------------|
| `content-service` | 8081 | Movie catalog — add movies, search, genres |
| `video-service` | 8082 | Upload raw video to AWS S3 + publish Kafka event |
| `encoding-service` | 8083 | FFmpeg — encode to 4 qualities + generate HLS |
| `streaming-service` | 8084 | Generate signed URLs + serve HLS playlists |

## 🔧 Tech Stack
- **Spring Boot 3.2** — Microservices framework
- **Apache Kafka** — Event streaming between services
- **AWS S3** — Video storage (raw + encoded)
- **FFmpeg** — Video encoding to multiple qualities
- **Redis** — Streaming URL cache
- **MySQL** — Movie catalog storage
- **Docker + Docker Compose** — Infrastructure setup
- **HLS.js** — Custom video player

## 📋 Prerequisites
Before running this project make sure you have:
- ✅ Java 17 / 21
- ✅ Maven
- ✅ Docker Desktop
- ✅ FFmpeg installed
- ✅ AWS Account with S3 bucket

### Install FFmpeg
**Windows:**
```bash
winget install ffmpeg
```
**Mac:**
```bash
brew install ffmpeg
```
Verify:
```bash
ffmpeg -version
```

## ⚙️ AWS S3 Setup
**Step 1: Create S3 Bucket**
- AWS Console → S3 → Create Bucket
- Name: `shoppable-streaming-videos`
- Region: `your-region`

**Step 2: Block Public Access Settings**
- Permissions → Block public access

**Step 3: Create IAM User**
- IAM → Users → Create User
- Name: `shoppable-app-user`
- Policy: `AmazonS3FullAccess`
- Create Access Key → Save both keys

## 🚀 How To Run

**Step 1: Configure AWS credentials**
Update `application.yml` in `video-service`, `encoding-service` and `streaming-service`:
```yaml
aws:
  access-key: YOUR_ACCESS_KEY
  secret-key: YOUR_SECRET_KEY
  region: YOUR_REGION
  s3:
    bucket-name: YOUR_BUCKET_NAME
```

**Step 2: Start Infrastructure**
```bash
docker-compose up -d
```
Wait 30 seconds for Kafka to fully initialize.

**Step 3: Start All Services**
Open 4 separate terminals:

```bash
# Terminal 1
cd content-service && mvn spring-boot:run

# Terminal 2
cd video-service && mvn spring-boot:run

# Terminal 3
cd encoding-service && mvn spring-boot:run

# Terminal 4
cd streaming-service && mvn spring-boot:run
```

## 🧪 Testing Flow

**Step 1: Add a Movie**
`POST http://localhost:8081/api/v1/movies`
```json
Content-Type: application/json

{
    "title": "Inception",
    "description": "A mind bending thriller",
    "genre": "SCI_FI",
    "director": "Christopher Nolan",
    "cast": "Leonardo DiCaprio",
    "releaseYear": 2010,
    "rating": 8.8,
    "durationMinutes": 148
}
```
Copy the id from response.

**Step 2: Upload Video**
`POST http://localhost:8082/api/v1/videos/upload/{movieId}`
`Content-Type: multipart/form-data`
`file: [select any mp4 video]`

**Step 3: Watch Encoding Service Logs**
```text
Consumed VideoUploadedEvent for movie: xxx
Running FFmpeg for 1080p...
Encoded 1080p successfully
Running FFmpeg for 720p...
Encoded 720p successfully
Running FFmpeg for 480p...
Encoded 480p successfully
Running FFmpeg for 360p...
Encoded 360p successfully
Master playlist generated
All encoded files uploaded to S3 ✅
VideoEncodedEvent published ✅
```

**Step 4: Check Movie Status**
`GET http://localhost:8081/api/v1/movies/{movieId}`
Response should show:
```json
{
    "videoStatus": "READY",
    "hlsUrl": "https://your-bucket.s3.region.amazonaws.com/encoded/movieId/master.m3u8"
}
```

**Step 5: Get Streaming URL**
`GET http://localhost:8084/api/v1/stream/{movieId}`
Response:
```json
{
    "movieId": "xxx",
    "streamingUrl": "https://your-bucket.s3.amazonaws.com/...",
    "quality": "1080p, 720p, 480p, 360p",
    "expiresInMinutes": 60
}
```

**Step 6: Play Video**
- Open `shoppable-stream.html` in Chrome
- Enter Movie ID
- Click Play
- Video streams in 1080p, 720p, 480p, 360p automatically ✅

## 🎬 Custom Shoppable-Streaming Player
We built a custom HLS player that:
- Calls Streaming Service automatically
- Signs every HLS segment individually
- Supports adaptive bitrate — switches quality based on internet speed
- Works with private S3 bucket

> ⚠️ **Important:** Third party HLS players (like hls-js.netlify.app, LiveReacting) will NOT work because they cannot sign individual segment requests. Use our `shoppable-stream.html` only.

## 📂 Project Structure
```text
Shopy-stream-app/
├── content-service/          → Movie catalog
├── video-service/            → S3 upload + Kafka
├── encoding-service/         → FFmpeg + HLS
├── streaming-service/        → Signed URLs + Redis
├── shoppable-stream.html     → Custom HLS video player
├── docker-compose.yml        → Infrastructure
└── README.md
```

## 🔑 Kafka Topics
| Topic | Publisher | Consumer |
|-------|-----------|----------|
| `video.uploaded` | Video Service | Encoding Service, Content Service |
| `video.encoded` | Encoding Service | Streaming Service, Content Service |

## 🔒 Security
- **Private S3 bucket** — videos not publicly accessible
- **Signed URLs** — every HLS segment signed individually
- **URL expiry** — 60 minutes
- **Raw videos** — completely private, only encoded folder accessible

## 📱 API Endpoints

### Content Service (8081)
- `POST   /api/v1/movies`              → Add movie
- `GET    /api/v1/movies`              → Get all movies
- `GET    /api/v1/movies/{id}`         → Get movie by ID
- `GET    /api/v1/movies/genre/{genre}` → Get by genre
- `GET    /api/v1/movies/search`       → Search by title

### Video Service (8082)
- `POST   /api/v1/videos/upload/{movieId}` → Upload video

### Streaming Service (8084)
- `GET    /api/v1/stream/{movieId}`           → Get streaming URL
- `GET    /api/v1/stream/{movieId}/playlist`  → Get signed playlist

## 🌟 Future Enhancements
- **Interactive Shoppable Overlay**: Real-time product pop-ups synced to video timestamps with haptic mobile feedback for a tactile shopping experience.
- **Analytics Dashboard**: Tracking video views, buffering events, shopping conversions, and user engagement.
- **Content Recommendation Engine**: Suggesting new videos and products based on user watch history.
- **Enhanced Security**: Implementing DRM (Digital Rights Management) for premium content.

## 🤝 Contributing
Contributions, issues, and feature requests are welcome! Feel free to check the issues page if you want to contribute.

## 💡 Acknowledgements
Building this platform was an incredible journey into the world of distributed systems and video engineering. A huge thank you to the open-source community for the amazing tools like FFmpeg, Kafka, and Spring Boot that make building systems at this scale possible!

---
*If you found this project interesting or helpful, don't forget to leave a ⭐!*
