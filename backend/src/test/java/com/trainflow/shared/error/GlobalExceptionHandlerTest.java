package com.trainflow.shared.error;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import org.springframework.web.HttpMediaTypeNotSupportedException;
import org.springframework.web.multipart.MaxUploadSizeExceededException;
import org.springframework.web.multipart.support.MissingServletRequestPartException;

class GlobalExceptionHandlerTest {
    private final GlobalExceptionHandler handler = new GlobalExceptionHandler();

    @Test
    void mapsMissingCvFileToAValidationError() {
        var response = handler.handleMissingPart(new MissingServletRequestPartException("file"));
        assertThat(response.getStatusCode().value()).isEqualTo(422);
        assertThat(response.getBody().code()).isEqualTo("FILE_REQUIRED");
    }

    @Test
    void mapsOversizedCvFileToPayloadTooLarge() {
        var response = handler.handleMaxUploadSize(new MaxUploadSizeExceededException(10));
        assertThat(response.getStatusCode().value()).isEqualTo(413);
        assertThat(response.getBody().code()).isEqualTo("FILE_TOO_LARGE");
    }

    @Test
    void mapsUploadWithoutMultipartContentToAFileError() {
        var response = handler.handleUnsupportedMediaType(new HttpMediaTypeNotSupportedException("Content-Type missing"));
        assertThat(response.getStatusCode().value()).isEqualTo(415);
        assertThat(response.getBody().code()).isEqualTo("FILE_REQUIRED");
    }
}
