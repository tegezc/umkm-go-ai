// File: mobile_app/lib/data/services/api_service.dart

import 'dart:convert';
import 'package:file_picker/file_picker.dart';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';

class ApiService {
  // static const String _baseUrl =
  //     "https://umkm-go-ai-api-102863217534.asia-southeast1.run.app/api/v1";
  // static const String _baseUrl = "http://10.0.2.2:8000/api/v1";
  static const String _baseUrl = "http://127.0.0.1:8000/api/v1";

  Future<Map<String, dynamic>> askOrchestrator(String query) async {
    final url = Uri.parse('$_baseUrl/orchestrator/query');

    try {
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'query': query, 'user_id': 'flutter_client_01'}),
      );

      if (response.statusCode == 200) {
        return json.decode(utf8.decode(response.bodyBytes));
      } else {
        final errorBody = json.decode(utf8.decode(response.bodyBytes));
        throw Exception(
          'Orchestrator failed. Status: ${response.statusCode}, Detail: ${errorBody['detail']}',
        );
      }
    } catch (e) {
      print('Error in askOrchestrator: $e');
      throw Exception('Failed to connect to the server: $e');
    }
  }

  // Fungsi untuk bertanya ke Agen Legalitas
  Future<Map<String, dynamic>> askLegalAgent(String query) async {
    final url = Uri.parse('$_baseUrl/legal/query');

    try {
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'query': query, 'user_id': 'flutter_client_01'}),
      );

      if (response.statusCode == 200) {
        // Jika server mengembalikan respons OK, parse JSON.
        return json.decode(utf8.decode(response.bodyBytes));
      } else {
        // Jika server mengembalikan error, lempar exception.
        throw Exception(
          'Failed to get answer from Legal Agent. Status code: ${response.statusCode}',
        );
      }
    } catch (e) {
      // Menangani error koneksi atau lainnya.
      print('Error in askLegalAgent: $e');
      throw Exception('Failed to connect to the server: $e');
    }
  }

  // Fungsi untuk bertanya ke Agen Pemasaran
  Future<Map<String, dynamic>> askMarketingAgent(String query) async {
    final url = Uri.parse('$_baseUrl/marketing/query');

    try {
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'query': query, 'user_id': 'flutter_client_01'}),
      );

      if (response.statusCode == 200) {
        return json.decode(utf8.decode(response.bodyBytes));
      } else {
        throw Exception(
          'Failed to get answer from Marketing Agent. Status code: ${response.statusCode}',
        );
      }
    } catch (e) {
      print('Error in askMarketingAgent: $e');
      throw Exception('Failed to connect to the server: $e');
    }
  }

  Future<Map<String, dynamic>> analyzeSalesData(PlatformFile file) async {
    final url = Uri.parse('$_baseUrl/agent/operational/analyze');

    try {
      // Membuat multipart request, yang dibutuhkan untuk file upload
      var request = http.MultipartRequest('POST', url);

      // Menambahkan file ke request
      request.files.add(
        http.MultipartFile.fromBytes(
          'file', // Nama field ini ('file') harus cocok dengan di backend FastAPI
          file.bytes!,
          filename: file.name,
          contentType: MediaType('text', 'csv'),
        ),
      );

      print("Sending file '${file.name}' to operational agent...");
      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        return json.decode(utf8.decode(response.bodyBytes));
      } else {
        final errorBody = json.decode(utf8.decode(response.bodyBytes));
        throw Exception(
          'Failed to analyze data. Status: ${response.statusCode}, Detail: ${errorBody['detail']}',
        );
      }
    } catch (e) {
      print('Error in analyzeSalesData: $e');
      throw Exception('Failed to connect to the server: $e');
    }
  }

  Future<Map<String, dynamic>> generateBrandKit(PlatformFile imageFile, String businessName) async {
    // Target endpoint Agen Merek
    final url = Uri.parse('$_baseUrl/agent/brand/generate_kit');

    try {
      var request = http.MultipartRequest('POST', url);

      // Tambahkan nama bisnis sebagai field
      request.fields['business_name'] = businessName;

      // 1. Dapatkan PATH file di cache (misal: /.../cache/file.tmp)
      final String imagePath = imageFile.path!;

      // 2. Dapatkan NAMA file ASLI (misal: "foto_liburan.jpg")
      final String originalFilename = imageFile.name;

      // 3. Dapatkan EKSTENSI file ASLI (misal: "jpg")
      final String extension = imageFile.extension ?? 'jpeg'; // Fallback

      // Gunakan fromPath (hemat memori) TAPI isi parameter lainnya
      request.files.add(
        await http.MultipartFile.fromPath(
          'file', // Nama field backend
          imagePath, // Path ke file di cache

          // WAJIB: Beri tahu nama file aslinya
          filename: originalFilename,

          // WAJIB: Set Content-Type secara manual
          contentType: MediaType('image', extension),
        ),
      );

      print("Sending image '$imagePath' to Brand Agent...");
      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        return json.decode(utf8.decode(response.bodyBytes));
      } else {
        final errorBody = json.decode(utf8.decode(response.bodyBytes));
        // Berikan pesan error yang lebih spesifik
        throw Exception('Failed to generate brand kit. Status: ${response.statusCode}, Detail: ${errorBody['detail']}');
      }
    } catch (e) {
      print('Error in generateBrandKit: $e');
      throw Exception('Failed to connect to the server: $e');
    }
  }
}
