package com.shopy_stream.contentservice.controller;

import com.shopy_stream.contentservice.dto.MovieRequest;
import com.shopy_stream.contentservice.dto.MovieResponse;
import com.shopy_stream.contentservice.model.Genre;
import com.shopy_stream.contentservice.service.ContentService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/movies")
@Slf4j
@RequiredArgsConstructor
public class ContentController {

    private final ContentService contentService;

    // Add new movie to catalog
    @PostMapping
    public ResponseEntity<MovieResponse> addMovie(
            @Valid @RequestBody MovieRequest movieRequest) {
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(contentService.addMovie(movieRequest));
    }

    // Get all movies
    @GetMapping
    public ResponseEntity<List<MovieResponse>> getAllMovies() {
        return ResponseEntity.ok(contentService.getAllMovies());
    }

    @GetMapping("/genre/{genre}")
    public ResponseEntity<List<MovieResponse>> getMoviesByGenre(
            @PathVariable Genre genre) {
        return ResponseEntity.ok(contentService.getMoviesByGenre(genre));
    }

    @GetMapping("/{movieId}")
    public ResponseEntity<MovieResponse> getMoviesById(
            @PathVariable String movieId) {
        return ResponseEntity.ok(contentService.getMovieById(movieId));
    }

    @GetMapping("/search")
    public ResponseEntity<List<MovieResponse>> searchMovie(
            @RequestParam String title) {
        return ResponseEntity.ok(contentService.searchMovies(title));
    }
}