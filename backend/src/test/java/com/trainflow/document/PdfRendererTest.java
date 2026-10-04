package com.trainflow.document;
import static org.junit.jupiter.api.Assertions.*; import java.util.Map; import org.apache.pdfbox.Loader; import org.junit.jupiter.api.Test;
class PdfRendererTest {@Test void generatesReadablePdfForEveryType()throws Exception{var renderer=new PdfRenderer();for(var type:DocumentType.values()){var bytes=renderer.render(type,Map.of("reference","TR-1","theme","Cybersecurity"));assertTrue(bytes.length>500);try(var pdf=Loader.loadPDF(bytes)){assertEquals(1,pdf.getNumberOfPages());}}}}
