package com.shopy_stream.contentservice.model;

public enum VideoStatus {
    PENDING, // movie added but not uploaded yet no usage
    UPLOADED, // raw video uploaded to S3 manage
    ENCODING, // FFmeg is encoding the video no usage
    ENCODED, // Encodinhg complete no usage
    READY, // HLS playlist ready - can be streamed no usages
    FAILED // Encoding Failed no usage
}
