// File: mobile_app/lib/data/services/api_service.dart

import 'dart:convert';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';

class ApiService {
  static String get _baseUrl {
    if (kIsWeb) {
      // Jika berjalan di web (Chrome, etc.)
      return "http://localhost:8000/api/v1/agent";
    } else {
      // Jika berjalan di mobile (asumsi Emulator Android)
      return "http://10.0.2.2:8000/api/v1/agent";
    }
  }

  // Fungsi untuk bertanya ke Agen Legalitas
  Future<Map<String, dynamic>> askLegalAgent(String query) async {
    final url = Uri.parse('$_baseUrl/legal/query');

    try {
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'query': query,
          'user_id': 'flutter_client_01',
        }),
      );

      if (response.statusCode == 200) {
        // Jika server mengembalikan respons OK, parse JSON.
        return json.decode(utf8.decode(response.bodyBytes));
      } else {
        // Jika server mengembalikan error, lempar exception.
        throw Exception('Failed to get answer from Legal Agent. Status code: ${response.statusCode}');
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
        body: json.encode({
          'query': query,
          'user_id': 'flutter_client_01',
        }),
      );

      if (response.statusCode == 200) {
        return json.decode(utf8.decode(response.bodyBytes));
      } else {
        throw Exception('Failed to get answer from Marketing Agent. Status code: ${response.statusCode}');
      }
    } catch (e) {
      print('Error in askMarketingAgent: $e');
      throw Exception('Failed to connect to the server: $e');
    }
  }

  Future<Map<String, dynamic>> analyzeSalesData(PlatformFile file) async {
    final url = Uri.parse('$_baseUrl/operational/analyze');

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
        throw Exception('Failed to analyze data. Status: ${response.statusCode}, Detail: ${errorBody['detail']}');
      }
    } catch (e) {
      print('Error in analyzeSalesData: $e');
      throw Exception('Failed to connect to the server: $e');
    }
  }
}