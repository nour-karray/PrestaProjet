package com.trainflow.trainer;
import static org.assertj.core.api.Assertions.*; import com.trainflow.shared.error.ApiError; import java.io.*; import java.util.zip.*; import org.junit.jupiter.api.*; import org.junit.jupiter.api.io.TempDir; import org.springframework.mock.web.MockMultipartFile;
class CvStorageServiceTest {
 @TempDir java.nio.file.Path temp;
 @Test void storesValidDocxAndRejectsDuplicateExtension() throws Exception {CvStorageService service=new CvStorageService(temp.toString(),10);byte[] content=docx();var stored=service.store(new MockMultipartFile("file","cv.docx","application/vnd.openxmlformats-officedocument.wordprocessingml.document",content));assertThat(service.resolve(stored.stored())).exists();assertThatThrownBy(()->service.store(new MockMultipartFile("file","cv.pdf.exe","application/pdf","%PDF-x".getBytes()))).isInstanceOf(ApiError.class);}
 private byte[] docx() throws Exception {var out=new ByteArrayOutputStream();try(var zip=new ZipOutputStream(out)){zip.putNextEntry(new ZipEntry("word/document.xml"));zip.write("<document/>".getBytes());zip.closeEntry();}return out.toByteArray();}
}
