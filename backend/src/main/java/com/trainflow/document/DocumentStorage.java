package com.trainflow.document;

import java.io.IOException;
import java.nio.file.*;
import java.security.*;
import java.util.HexFormat;
import java.util.UUID;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Component
public class DocumentStorage {
 public record Stored(String relativePath,String filename,long size,String sha256){}
 private final Path root; private final long maximum;
 public DocumentStorage(@Value("${trainflow.storage.document-directory}") String path,@Value("${trainflow.storage.max-document-size-mb:10}") long mb){root=Path.of(path).toAbsolutePath().normalize();maximum=mb*1024*1024;}
 public Stored store(UUID caseId,DocumentType type,byte[] content) throws IOException {if(content.length==0||content.length>maximum)throw new IllegalArgumentException("Invalid document size");Path directory=safe(caseId.toString(),type.name().toLowerCase());Files.createDirectories(directory);String filename=UUID.randomUUID()+".pdf";Path destination=safe(caseId.toString(),type.name().toLowerCase(),filename);Path temporary=Files.createTempFile(directory,".tmp-",".pdf");try{Files.write(temporary,content);try{Files.move(temporary,destination,StandardCopyOption.ATOMIC_MOVE);}catch(AtomicMoveNotSupportedException e){Files.move(temporary,destination,StandardCopyOption.REPLACE_EXISTING);}return new Stored(root.relativize(destination).toString().replace('\\','/'),filename,content.length,sha256(content));}finally{Files.deleteIfExists(temporary);}}
 public Path resolve(String relative){if(relative==null||relative.isBlank()||Path.of(relative).isAbsolute())throw new IllegalArgumentException("Invalid document path");Path result=root.resolve(relative).normalize();if(!result.startsWith(root))throw new IllegalArgumentException("Invalid document path");return result;}
 public void delete(String relative){if(relative==null)return;try{Files.deleteIfExists(resolve(relative));}catch(IOException ignored){}}
 private Path safe(String... parts){Path p=root;for(String part:parts){if(part==null||part.isBlank()||!Path.of(part).getFileName().toString().equals(part)||part.contains(".."))throw new IllegalArgumentException("Invalid document path");p=p.resolve(part);}p=p.normalize();if(!p.startsWith(root))throw new IllegalArgumentException("Invalid document path");return p;}
 private static String sha256(byte[] bytes){try{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));}catch(NoSuchAlgorithmException e){throw new IllegalStateException(e);}}
}
