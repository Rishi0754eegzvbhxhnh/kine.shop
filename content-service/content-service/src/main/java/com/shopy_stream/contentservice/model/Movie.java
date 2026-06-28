package com.shopy_stream.contentservice.model;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import java.time.LocalDateTime;
import java.util.List;

@Entity
@Table(name = "movies")
@Data
@AllArgsConstructor
@NoArgsConstructor
public class Movie {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private String id;

    @Column(nullable = false)
    private String title;

    @Column(columnDefinition = "TEXT")
    private String description;

    @Enumerated(EnumType.STRING)
    private Genre genre;

    private String director;

    private String cast;

    private int releaseYear;

    private double rating;

    private String thumbnailUrl;

    private int durationMinutes;

    // S3 key of the raw uploaded video
    private String videoKey;

    // S3 key / URL of the encoded HLS master playlist
    private String hlsUrl;

    @Enumerated(EnumType.STRING)
    private VideoStatus videoStatus;

    @CreationTimestamp
    private LocalDateTime createdAt;

    @UpdateTimestamp
    private LocalDateTime updatedAt;
}
