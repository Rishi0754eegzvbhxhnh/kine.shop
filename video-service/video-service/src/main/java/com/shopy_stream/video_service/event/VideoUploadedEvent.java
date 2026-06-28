package com.shopy_stream.video_service.event;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Published to Kafka topic: video.uploaded
 * Consumed by Encoding Service to start FFmpeg processing.
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
public class VideoUploadedEvent {
    private String movieId;
    private String videoKey;
    private String bucketName;
    private String originalFileName;
    private long fileSizeBytes;
}
