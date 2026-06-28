package com.shopy_stream.contentservice.dto;

import com.shopy_stream.contentservice.model.Genre;
import jakarta.validation.constraints.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class MovieRequest {

    @NotBlank(message = "Title is required")
    private String title;

    private String description;

    @NotNull(message = "Genre is required")
    private Genre genre;

    private String director;

    private String cast;

    @Min(value = 1888, message = "Release year must be valid")
    private int releaseYear;

    @DecimalMin(value = "0.0", message = "Rating must be >= 0")
    @DecimalMax(value = "10.0", message = "Rating must be <= 10")
    private double rating;

    private String thumbnailUrl;

    @Positive(message = "Duration must be positive")
    private int durationMinutes;
}
